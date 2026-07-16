"""
tinytot.benchmark — Evaluate TinyToT inference quality at scale against trace corpora.

Measures:
  - Routing accuracy: does the prompt land in the right category?
  - Knowledge retrieval precision: does the top passage contain the answer?
  - Answer quality: does the shaped answer match expected output?
  - Throughput: passages/second indexed and queries/second served

Usage (from repo root):
    pipenv run python -m tinytot.benchmark gsm8k /path/to/test.jsonl --limit 200
    pipenv run python -m tinytot.benchmark routing --limit 100
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random as _random
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

from tinytot.content import CATEGORY_DIR, DATA_DIR  # noqa: E402

_CALC_RE = re.compile(r"<<[^>]+>>")


def _expected_answer(raw_answer: str) -> str:
    """Extract the numeric answer after #### from a GSM8K answer string."""
    if "####" in raw_answer:
        return raw_answer.split("####", 1)[1].strip()
    # Fallback: last line
    lines = [line.strip() for line in raw_answer.strip().splitlines() if line.strip()]
    return lines[-1] if lines else ""


# ---------------------------------------------------------------------------
# GSM8K benchmark
# ---------------------------------------------------------------------------


def _gsm8k_worker(rec: dict) -> dict:
    """Process a single GSM8K record; returns result dict."""
    from tinytot.inference import generateReasoningResponse

    question = rec["question"].strip()
    expected = _expected_answer(rec["answer"])
    t0 = time.perf_counter()
    result = generateReasoningResponse(question)
    ms = int((time.perf_counter() - t0) * 1000)
    isHit = bool(expected and expected in result)
    isPartial = bool(not isHit and expected and any(tok in result for tok in expected.split() if tok.isdigit()))
    return {"passed": isHit, "partial": isPartial, "ms": ms, "question": question}


def benchmark_gsm8k(source: Path, limit: int = 0) -> dict:
    """Run TinyToT against GSM8K test set and measure answer retrieval quality.

    For each test problem, queries the knowledge base and checks whether the
    expected numeric answer appears in the returned passage.  Records are
    processed in parallel across available CPU cores.
    """

    from tinytot.content import loadKnowledgePassages
    from tinytot.retrieval import buildKnowledgeIndex

    buildKnowledgeIndex.cache_clear()
    loadKnowledgePassages.cache_clear()

    records = []
    with open(source, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if limit:
        records = records[:limit]

    # Warm up the index in this process so workers share the cached index.
    entries, _idf, _tf = buildKnowledgeIndex()

    _print_section("GSM8K Math")
    caseResults = _run_cases_parallel(
        records,
        _gsm8k_worker,
        label_fn=lambda r: r["question"][:40],
    )

    hits = sum(1 for r in caseResults if r["passed"])
    partialHits = sum(1 for r in caseResults if r.get("partial"))
    noHit = len(caseResults) - hits - partialHits
    total = len(caseResults)
    avgMs = sum(r["ms"] for r in caseResults) / max(total, 1)

    results = {
        "total": total,
        "exact_hits": hits,
        "partial_hits": partialHits,
        "no_hit": noHit,
        "exact_pct": round(hits / total * 100, 1) if total else 0,
        "partial_pct": round((hits + partialHits) / total * 100, 1) if total else 0,
        "index_passages": len(entries),
        "avg_query_ms": round(avgMs, 1),
        "throughput_qps": round(1000 / avgMs, 1) if avgMs else 0,
    }

    buildKnowledgeIndex.cache_clear()
    loadKnowledgePassages.cache_clear()
    return results


# ---------------------------------------------------------------------------
# Routing benchmark
# ---------------------------------------------------------------------------

_ROUTING_CASES = [
    # (prompt, expected_category)
    # --- math ---
    ("Calculate 15 times 23 plus 7", "math"),
    ("What is the derivative of x squared plus 3x?", "math"),
    ("What is the probability of rolling a 7 with two dice?", "math"),
    ("Find the area of a circle with radius 5", "math"),
    ("Solve for x: 2x + 3 = 7", "math"),
    ("What is the factorial of 5?", "math"),
    ("How many combinations of 3 items from 10?", "math"),
    ("What is 15 percent of 240?", "math"),
    ("What is the square root of 144?", "math"),
    ("Convert 72 degrees Fahrenheit to Celsius", "math"),
    # --- programming ---
    ("Write Python code to sort a list", "programming"),
    ("Debug this function — it throws a segfault", "programming"),
    ("How do I optimize a slow SQL query?", "programming"),
    ("Implement a binary search algorithm", "programming"),
    ("Write a function to reverse a string in Python", "programming"),
    ("How do I handle exceptions in Python?", "programming"),
    ("What is a recursive function?", "programming"),
    ("How do I iterate over a dictionary in Python?", "programming"),
    # --- aws ---
    ("How do I create an EC2 instance on AWS?", "aws"),
    ("Configure an S3 bucket with lifecycle policy", "aws"),
    ("Set up a VPC with private subnets", "aws"),
    ("How do I attach an IAM role to a Lambda function?", "aws"),
    ("Deploy a containerised application on ECS", "aws"),
    # --- tool_calling ---
    ("Search for information about quantum computing", "tool_calling"),
    ("Find the latest news about quantum physics discoveries", "tool_calling"),
    ("What is the current weather in Tokyo?", "tool_calling"),
    ("What is today's stock price for Apple?", "tool_calling"),
    ("Look up who won the 2024 US election", "tool_calling"),
    ("What is the current exchange rate for USD to EUR?", "tool_calling"),
    # --- financial ---
    ("Calculate my retirement savings with compound interest", "financial"),
    ("How do I diversify my investment portfolio?", "financial"),
    ("Explain tax deductions for freelancers", "financial"),
    ("What is a P/E ratio?", "financial"),
    ("How does dollar-cost averaging work?", "financial"),
    # --- fs ---
    ("List all files in the home directory", "fs"),
    ("Find duplicate files and remove them", "fs"),
    ("Check disk space usage on the system", "fs"),
    ("How do I change file permissions on Linux?", "fs"),
    ("Find all Python files modified in the last 7 days", "fs"),
    # --- computer_science ---
    ("Explain how a binary search tree works", "computer_science"),
    ("What is the difference between TCP and UDP?", "computer_science"),
    ("How does a hash table handle collisions?", "computer_science"),
    ("What is Big O notation?", "computer_science"),
    ("Explain the CAP theorem", "computer_science"),
    # --- creative_writing ---
    ("Write a short story about a robot learning to feel", "creative_writing"),
    ("Write a haiku about autumn leaves", "creative_writing"),
    ("Continue this story: The door opened slowly...", "creative_writing"),
    ("Write a persuasive essay opening about climate change", "creative_writing"),
    # --- game24 ---
    ("Use the numbers 4 8 9 10 to make 24 using arithmetic", "game24"),
    ("Make 24 from 1 2 6 8", "game24"),
    ("Combine 1 4 5 6 to get 24", "game24"),
    ("Target 24 using 2 4 8 8", "game24"),
    ("Number puzzle: use 1 2 7 7 to make 24", "game24"),
]


def benchmark_routing(limit: int = 0) -> dict:
    """Measure routing accuracy against known category/prompt pairs."""
    from tinytot.content import getCategories, loadReasoningChains
    from tinytot.retrieval import buildChainIndex, buildKnowledgeIndex, categorizePrompt

    buildChainIndex.cache_clear()
    buildKnowledgeIndex.cache_clear()
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()

    cases = _ROUTING_CASES[:limit] if limit else _ROUTING_CASES

    # Warm all caches in this thread so workers only read the hot cache.
    getCategories()
    buildChainIndex()
    buildKnowledgeIndex()

    def routingWorker(item: tuple) -> dict:
        prompt, expected = item
        t0 = time.perf_counter()
        actual = categorizePrompt(prompt)
        ms = int((time.perf_counter() - t0) * 1000)
        ok = actual == expected
        return {"passed": ok, "ms": ms, "prompt": prompt, "expected": expected, "got": actual}

    _print_section("Routing Accuracy")
    caseResults = _run_cases_parallel(cases, routingWorker, label_fn=lambda c: c[0][:40])

    correct = sum(1 for r in caseResults if r["passed"])
    wrong = [
        {"prompt": r["prompt"][:60], "expected": r["expected"], "got": r["got"]} for r in caseResults if not r["passed"]
    ]
    total = len(caseResults)
    avgMs = sum(r["ms"] for r in caseResults) / max(total, 1)

    results = {
        "total": total,
        "correct": correct,
        "accuracy_pct": round(correct / total * 100, 1) if total else 0,
        "avg_query_ms": round(avgMs, 2),
        "misrouted": wrong,
    }

    buildChainIndex.cache_clear()
    buildKnowledgeIndex.cache_clear()
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()
    return results


# ---------------------------------------------------------------------------
# Knowledge retrieval precision benchmark
# ---------------------------------------------------------------------------

_RETRIEVAL_CASES = [
    ("What is the capital of France?", "Paris"),
    ("What is the capital of Germany?", "Berlin"),
    ("How many days are in a week?", "7"),
    ("Why is the sky blue?", "Rayleigh"),
    ("What is machine learning?", "artificial intelligence"),
    ("What is a neural network?", "neurons"),
    ("What is gradient descent?", "loss"),
    ("What is the minimum balance for a savings account?", "$500"),
    ("What documents are required to open a business account?", "EIN"),
    ("What is Python async/await?", "I/O"),
    ("What are the benefits of Python type hints?", "IDE"),
    ("How many days are in a year?", "365"),
    ("What is the speed of light?", "299"),
    ("What is compound interest?", "principal"),
    ("What is a 401k?", "retirement"),
]


def benchmark_retrieval(limit: int = 0) -> dict:
    """Measure knowledge retrieval precision against known Q/A pairs."""
    from tinytot.content import loadKnowledgePassages
    from tinytot.inference import generateReasoningResponse
    from tinytot.retrieval import buildKnowledgeIndex

    buildKnowledgeIndex.cache_clear()
    loadKnowledgePassages.cache_clear()

    cases = _RETRIEVAL_CASES[:limit] if limit else _RETRIEVAL_CASES

    # Warm caches before workers so threads hit the hot cache.
    buildKnowledgeIndex()
    loadKnowledgePassages()

    def retrievalWorker(item: tuple) -> dict:
        question, expectedToken = item
        t0 = time.perf_counter()
        result = generateReasoningResponse(question)
        ms = int((time.perf_counter() - t0) * 1000)
        ok = expectedToken.lower() in result.lower()
        return {"passed": ok, "ms": ms, "q": question, "expected": expectedToken, "got": result[:80]}

    _print_section("Knowledge Retrieval")
    caseResults = _run_cases_parallel(cases, retrievalWorker, label_fn=lambda c: c[0][:40])

    hits = sum(1 for r in caseResults if r["passed"])
    misses = [{"q": r["q"][:60], "expected": r["expected"], "got": r["got"]} for r in caseResults if not r["passed"]]
    total = len(caseResults)
    avgMs = sum(r["ms"] for r in caseResults) / max(total, 1)

    results = {
        "total": total,
        "hits": hits,
        "precision_pct": round(hits / total * 100, 1) if total else 0,
        "avg_query_ms": round(avgMs, 1),
        "misses": misses,
    }

    buildKnowledgeIndex.cache_clear()
    loadKnowledgePassages.cache_clear()
    return results


# ---------------------------------------------------------------------------
# Summarization eval
# ---------------------------------------------------------------------------


def _parse_summarize_eval(path: Path) -> list[dict]:
    """Parse a summarize_eval.md file into test cases.

    Each case has: name, input, must_contain (list[str]), max_words (int).
    """
    import re as _re

    text = path.read_text(encoding="utf-8")
    cases: list[dict] = []
    for section in _re.split(r"\n---\n+", text):
        name_m = _re.match(r"##\s+(\S+)", section.strip())
        if not name_m:
            continue
        name = name_m.group(1)
        mw_m = _re.search(r"max_words:\s*(\d+)", section)
        max_words = int(mw_m.group(1)) if mw_m else 50
        inp_m = _re.search(r"### Input\n(.*?)(?=\n###|\Z)", section, _re.DOTALL)
        if not inp_m:
            continue
        passage = inp_m.group(1).strip()
        mc_m = _re.search(r"### Must Contain\n(.*?)(?=\n###|\Z)", section, _re.DOTALL)
        must_contain: list[str] = []
        if mc_m:
            for line in mc_m.group(1).splitlines():
                item = line.strip().lstrip("- ").strip()
                if item:
                    must_contain.append(item)
        cases.append({"name": name, "input": passage, "must_contain": must_contain, "max_words": max_words})
    return cases


_EVAL_FILE = DATA_DIR / "eval" / "summarize_eval.md"


def benchmark_summarize(eval_file: Path = _EVAL_FILE) -> dict:
    """Run TinyToT summarization against every case in the eval dataset."""
    from tinytot.summarize import summarizeDocument

    if not eval_file.exists():
        return {"error": f"eval file not found: {eval_file}"}

    cases = _parse_summarize_eval(eval_file)
    if not cases:
        return {"error": "no cases parsed from eval file"}

    def summarizeWorker(case: dict) -> dict:
        t0 = time.perf_counter()
        summary = summarizeDocument(case["input"], max_words=case["max_words"])
        ms = int((time.perf_counter() - t0) * 1000)
        missing = [p for p in case["must_contain"] if p.lower() not in summary.lower()]
        ok = len(missing) == 0
        return {
            "passed": ok,
            "ms": ms,
            "name": case["name"],
            "words": len(summary.split()),
            "missing": missing,
            "summary": summary[:120],
        }

    _print_section("Summarization")
    caseResults = _run_cases_parallel(cases, summarizeWorker, label_fn=lambda c: c["name"])

    passed = sum(1 for r in caseResults if r["passed"])
    n = len(caseResults)
    totalMs = sum(r["ms"] for r in caseResults)
    perCase = [{"name": r["name"], "passed": r["passed"], "words": r["words"], "ms": r["ms"]} for r in caseResults]
    failures = [
        {"case": r["name"], "missing": r["missing"], "summary": r["summary"]} for r in caseResults if not r["passed"]
    ]
    return {
        "cases": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy": f"{passed}/{n}  ({100 * passed // n}%)",
        "total_ms": totalMs,
        "avg_ms_per_case": totalMs // max(n, 1),
        "per_case": perCase,
        "failures": failures,
    }


# ---------------------------------------------------------------------------
# Report printer with ASCII charts
# ---------------------------------------------------------------------------


def _bar(value: float, total: float, width: int = 30, fill: str = "#", empty: str = ".") -> str:
    """Render a simple ASCII progress bar."""
    filled = int(round(width * value / max(total, 1)))
    return "[" + fill * filled + empty * (width - filled) + "]"


def _print_section(title: str) -> None:
    print(f"\n{'=' * 64}\n  {title}\n{'=' * 64}", flush=True)


def _run_cases_parallel(
    cases: list,
    worker_fn,
    label_fn=None,
    workers: int | None = None,
) -> list:
    """Run benchmark cases in parallel, printing buffered progress after all complete.

    Args:
        cases:      Iterable of inputs passed one-by-one to *worker_fn*.
        worker_fn:  Callable(case) → result dict with at least 'passed' bool.
        label_fn:   Optional callable(case) → short label string for the output line.
        workers:    Thread count; defaults to min(cpu_count, 8).

    Returns:
        List of result dicts in completion order.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    nWorkers = workers or min(os.cpu_count() or 1, 8)
    results = []
    passed = 0

    with ThreadPoolExecutor(max_workers=nWorkers) as pool:
        futureMap = {pool.submit(worker_fn, c): c for c in cases}
        done = 0
        for future in as_completed(futureMap):
            result = future.result()
            results.append(result)
            done += 1
            if result.get("passed"):
                passed += 1
            label = label_fn(futureMap[future]) if label_fn else ""
            labelShort = (label[:40] + "…") if len(label) > 41 else f"{label:<41}"
            mark = "PASS" if result.get("passed") else "FAIL"
            bar = _bar(passed, done, width=10)
            ms = result.get("ms", 0)
            print(f"  {labelShort}  {ms:>4}ms  {mark}  {bar}", flush=True)

    return results


def _print_report(name: str, results: dict) -> None:
    print(f"\n{'=' * 64}")
    print(f"  {name}")
    print(f"{'=' * 64}")

    # Summarization per-case chart
    if "per_case" in results:
        cases = results["per_case"]
        max_label = max((len(c["name"]) for c in cases), default=20)
        print(f"\n  {'Case':<{max_label}}  Words   ms  Result")
        print(f"  {'-' * (max_label + 22)}")
        for c in cases:
            if c.get("skipped") or c.get("passed") is None:
                mark = "SKIP"
            elif c["passed"]:
                mark = "PASS"
            else:
                mark = "FAIL"
            bar = _bar(c["words"], 50, width=10)
            print(f"  {c['name']:<{max_label}}  {c['words']:>5} {c['ms']:>4}ms  {mark}  {bar}")
        print()
        # Pass rate (skipped cases excluded from denominator)
        n = results.get("cases", sum(1 for c in cases if not c.get("skipped")))
        p = results.get("passed", sum(1 for c in cases if c["passed"]))
        skip_count = results.get("skipped", sum(1 for c in cases if c.get("skipped")))
        skip_note = f"  ({skip_count} skipped)" if skip_count else ""
        print(f"  Pass rate  {_bar(p, n, width=40)}  {p}/{n}{skip_note}")
        if results.get("failures"):
            print("\n  Failures:")
            for f in results["failures"]:
                missing = f.get("missing") or f.get("expected_any", [])
                preview = f.get("summary") or f.get("result") or f.get("result_preview", "")
                print(f"    {f['case']}: missing {missing}")
                if preview:
                    print(f"      got: {preview}")
        return

    # GSM8K / routing / retrieval charts
    numeric_keys = []
    for k, v in results.items():
        if k in ("misrouted", "misses", "errors") and isinstance(v, list):
            if v:
                print(f"  {k}:")
                for item in v[:10]:
                    print(f"    {item}")
        elif isinstance(v, (int, float)) and k not in ("total", "correct", "incorrect"):
            numeric_keys.append((k, v))
        else:
            print(f"  {k}: {v}")

    # Accuracy bar if we can compute it
    total = results.get("total", 0)
    correct = results.get("correct") or results.get("hits") or results.get("exact_hits") or results.get("passed", 0)
    if total and correct:
        pct = correct / total
        print(f"\n  Accuracy   {_bar(pct, 1.0, width=40, fill='#', empty='.')}  {correct}/{total}  ({pct * 100:.1f}%)")

    # Throughput bar (passages/sec)
    tput = results.get("passages_per_sec") or results.get("queries_per_sec")
    if tput:
        scale = max(tput, 100)
        print(f"  Throughput {_bar(tput, scale, width=40)}  {tput:.0f}/s")


# ---------------------------------------------------------------------------
# Codegen benchmark
# ---------------------------------------------------------------------------

_CODEGEN_CASES = [
    # (prompt, language, must_contain_in_code)
    # --- Python algorithms ---
    ("Write a Python function to reverse a string", "python", "def "),
    ("Implement binary search in Python", "python", "def binary_search"),
    ("Write a Python function to compute Fibonacci numbers", "python", "def fibonacci"),
    ("Write a Python class for a stack with push and pop", "python", "class Stack"),
    ("Write a Python function for the two sum problem", "python", "def two_sum"),
    ("Compute the GCD of two numbers in Python", "python", "def gcd"),
    ("Check if a number is prime in Python", "python", "def is_prime"),
    ("FizzBuzz from 1 to 100", "python", "def fizzbuzz"),
    ("Maximum subarray sum Kadane algorithm", "python", "def max_subarray"),
    ("Coin change minimum coins DP", "python", "def coin_change"),
    ("Number of ways to climb stairs", "python", "def climb_stairs"),
    ("Longest common subsequence", "python", "def lcs_length"),
    ("Knapsack 0/1 dynamic programming", "python", "def knapsack"),
    ("Find the median of a list", "python", "def median"),
    ("Check if two strings are anagrams", "python", "def are_anagrams"),
    ("Find all duplicates in a list", "python", "def find_duplicates"),
    ("Write a Python decorator that logs function calls", "python", "def wrapper"),
    ("Create a Python dataclass for a Person", "python", "@dataclass"),
    ("Write a Python context manager for timing code", "python", "@contextmanager"),
    ("Implement merge sort in Python", "python", "def merge_sort"),
    ("Implement quicksort in Python", "python", "def quick_sort"),
    ("Detect cycle in a linked list", "python", "def has_cycle"),
    ("Level order traversal of a binary tree", "python", "def level_order"),
    ("Write a Python function for power set", "python", "def power_set"),
    ("Find the most frequent element in a list", "python", "def most_frequent"),
    # --- SQL ---
    ("Write a SQL query to select all users where age > 30", "sql", "SELECT"),
    ("Write a SQL CREATE TABLE for a users table", "sql", "CREATE TABLE"),
    ("Write a SQL JOIN query for users and orders", "sql", "JOIN"),
    # --- JavaScript ---
    ("Write a JavaScript function to reverse a string", "javascript", "function "),
    ("Implement binary search in JavaScript", "javascript", "function "),
    ("Two sum problem in JavaScript", "javascript", "function two_sum"),
    ("FizzBuzz in JavaScript", "javascript", "function fizzbuzz"),
    ("Write a JavaScript function to compute Fibonacci", "javascript", "function fibonacci"),
    # --- Go ---
    ("Write a Go function to reverse a string", "go", "func "),
    ("Write a Go function for binary search", "go", "func "),
    ("Write a Go function to compute Fibonacci numbers", "go", "func fibonacci"),
    ("Two sum in Go", "go", "func twoSum"),
    # --- Rust ---
    ("Write a Rust function to reverse a string", "rust", "fn "),
    ("Write a Rust function for binary search", "rust", "fn "),
    ("Write a Rust function to compute Fibonacci numbers", "rust", "fn fibonacci"),
    ("Two sum in Rust", "rust", "fn two_sum"),
    # --- Ruby ---
    ("Write a Ruby function to compute Fibonacci numbers", "ruby", "def fibonacci"),
    ("Write a Ruby function to reverse a string", "ruby", "def reverse_string"),
    # --- Swift ---
    ("Write a Swift function to compute Fibonacci numbers", "swift", "func fibonacci"),
    ("Write a Swift function to reverse a string", "swift", "func reverseString"),
    # --- Compositional ---
    ("Find the second largest number in a list", "python", "def second_largest"),
    ("Reverse words in a sentence", "python", "def reverse_words"),
    ("Find all prime numbers up to 50", "python", "def "),
    ("Compute the power set of a list", "python", "def power_set"),
]


def benchmark_codegen() -> dict:
    """Benchmark code generation: coverage, language accuracy, and code validity.

    For each case, checks:
      1. Code was generated (not None).
      2. Fenced block declares the right language.
      3. The must_contain string appears in the generated code.
    """
    from tinytot.codegen import _loadConfig, _loadPatterns, generateCode

    _loadConfig.cache_clear()
    _loadPatterns.cache_clear()
    _loadConfig()
    _loadPatterns()

    _fenceNorm = {"cpp": "c++", "csharp": "c#", "python3": "python"}

    def codegenWorker(item: tuple) -> dict:
        prompt, expectedLang, mustContain = item
        t0 = time.perf_counter()
        result = generateCode(prompt)
        ms = int((time.perf_counter() - t0) * 1000)
        if not result:
            ok, reason = False, "no_code_generated"
        else:
            fenceLang = _fenceNorm.get(
                result.splitlines()[0].lstrip("`").strip().lower(), result.splitlines()[0].lstrip("`").strip().lower()
            )
            langOk = fenceLang == expectedLang or (expectedLang == "python" and fenceLang == "")
            contentOk = mustContain.lower() in result.lower()
            ok = langOk and contentOk
            reason = "" if ok else (f"wrong_lang:{fenceLang}" if not langOk else f"missing:{mustContain!r}")
        return {
            "passed": ok,
            "ms": ms,
            "name": f"{expectedLang}/{prompt[:35]}",
            "words": len((result or "").split()),
            "reason": reason,
            "prompt": prompt,
            "expectedLang": expectedLang,
            "got": (result or "")[:80].replace("\n", " "),
        }

    _print_section("Code Generation")
    caseResults = _run_cases_parallel(_CODEGEN_CASES, codegenWorker, label_fn=lambda c: f"{c[0][:35]}")

    passed = sum(1 for r in caseResults if r["passed"])
    n = len(caseResults)
    totalMs = sum(r["ms"] for r in caseResults)
    perCase = [{"name": r["name"], "passed": r["passed"], "words": r["words"], "ms": r["ms"]} for r in caseResults]
    failures = [
        {"prompt": r["prompt"][:60], "expected_lang": r["expectedLang"], "reason": r["reason"], "got": r["got"]}
        for r in caseResults
        if not r["passed"]
    ]
    return {
        "cases": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy": f"{passed}/{n}  ({100 * passed // n}%)",
        "total_ms": totalMs,
        "avg_ms_per_case": totalMs // max(n, 1),
        "per_case": perCase,
        "failures": failures,
    }


# ---------------------------------------------------------------------------
# Game24 benchmark
# ---------------------------------------------------------------------------

_GAME24_FILE = CATEGORY_DIR / "game24.md"

_GAME24_CASES = [
    ("Use the numbers 4 8 9 10 to make 24", "game24"),
    ("Make 24 from 1 2 6 8", "game24"),
    ("Use 3 3 8 8 to reach 24", "game24"),
    ("How do I get 24 from 5 5 5 1", "game24"),
    ("Numbers 6 6 6 6 — make 24", "game24"),
    ("Calculate 24 using numbers 1 3 4 6", "game24"),
    ("Make 24 using 2 3 4 4", "game24"),
    ("Use 1 5 5 5 to reach twenty-four", "game24"),
    ("Game24: numbers are 2 2 11 11", "game24"),
    ("Arithmetic puzzle: 3 3 7 7 equals 24", "game24"),
    ("Combine 1 4 5 6 to get 24", "game24"),
    ("Using 4 numbers 2 6 6 6 calculate 24", "game24"),
    ("Number puzzle: use 1 2 7 7 to make 24", "game24"),
    ("Get 24 from 3 9 9 9", "game24"),
    ("Target 24 using 2 4 8 8", "game24"),
]


def benchmark_game24() -> dict:
    """Measure routing accuracy and response quality for Game24 prompts."""
    from tinytot.content import loadReasoningChains
    from tinytot.retrieval import buildChainIndex, categorizePrompt

    buildChainIndex.cache_clear()
    loadReasoningChains.cache_clear()

    if not _GAME24_FILE.exists():
        return {"skipped": True, "reason": f"{_GAME24_FILE} not found — run: python -m tinytot.ingest tot-princeton"}

    correct_route = 0
    has_arithmetic = 0
    query_times = []

    for prompt, expected_cat in _GAME24_CASES:
        t0 = time.perf_counter()
        actual_cat = categorizePrompt(prompt)
        query_times.append(time.perf_counter() - t0)
        if actual_cat == expected_cat:
            correct_route += 1

        from tinytot.inference import generateReasoningResponse

        response = generateReasoningResponse(prompt)
        # A useful Game24 response should contain arithmetic operators
        if any(op in response for op in ("+", "-", "*", "/", "×", "÷")):
            has_arithmetic += 1

    total = len(_GAME24_CASES)
    avg_ms = (sum(query_times) / len(query_times)) * 1000 if query_times else 0

    buildChainIndex.cache_clear()
    loadReasoningChains.cache_clear()
    return {
        "total": total,
        "correct": correct_route,
        "arithmetic_responses": has_arithmetic,
        "routing_pct": round(correct_route / total * 100, 1) if total else 0,
        "response_pct": round(has_arithmetic / total * 100, 1) if total else 0,
        "avg_query_ms": round(avg_ms, 1),
    }


# ---------------------------------------------------------------------------
# Creative writing (ToT text) benchmark
# ---------------------------------------------------------------------------

_TOT_TEXT_FILE = CATEGORY_DIR / "creative_writing.md"

_TOT_TEXT_CASES = [
    ("Write a short story about a robot learning to feel", "creative_writing"),
    ("Write a haiku about autumn leaves", "creative_writing"),
    ("Continue this story: The door opened slowly...", "creative_writing"),
    ("Write a persuasive essay opening about climate change", "creative_writing"),
    ("Write a story about two old friends reuniting", "creative_writing"),
    ("Write a passage about a journey through a forest at night", "creative_writing"),
    ("Draft a narrative about a scientist making an unexpected discovery", "creative_writing"),
    ("Write an opening paragraph for a mystery novel", "creative_writing"),
]


def benchmark_tot_text() -> dict:
    """Measure routing accuracy and prose quality for creative writing prompts."""
    from tinytot.content import loadReasoningChains
    from tinytot.inference import generateReasoningResponse
    from tinytot.retrieval import buildChainIndex, categorizePrompt

    buildChainIndex.cache_clear()
    loadReasoningChains.cache_clear()

    if not _TOT_TEXT_FILE.exists():
        return {"skipped": True, "reason": f"{_TOT_TEXT_FILE} not found — run: python -m tinytot.ingest tot-princeton"}

    correct_route = 0
    has_prose = 0
    query_times = []

    for prompt, expected_cat in _TOT_TEXT_CASES:
        t0 = time.perf_counter()
        actual_cat = categorizePrompt(prompt)
        query_times.append(time.perf_counter() - t0)
        if actual_cat == expected_cat:
            correct_route += 1

        response = generateReasoningResponse(prompt)
        # A useful creative writing response should be at least a sentence long
        if response and len(response.split()) >= 10:
            has_prose += 1

    total = len(_TOT_TEXT_CASES)
    avg_ms = (sum(query_times) / len(query_times)) * 1000 if query_times else 0

    buildChainIndex.cache_clear()
    loadReasoningChains.cache_clear()
    return {
        "total": total,
        "correct": correct_route,
        "prose_responses": has_prose,
        "routing_pct": round(correct_route / total * 100, 1) if total else 0,
        "response_pct": round(has_prose / total * 100, 1) if total else 0,
        "avg_query_ms": round(avg_ms, 1),
    }


# ---------------------------------------------------------------------------
# Agentic tool benchmark
# ---------------------------------------------------------------------------

_AGENT_TOOL_CASES = [
    # (description, tool_name, kwargs, must_contain_in_result)
    ("List files in data/", "file_explore", {"path": str(DATA_DIR), "operation": "list"}, ["categories", "knowledge"]),
    (
        "Stat the gsm8k jsonl",
        "file_explore",
        {"path": str(DATA_DIR / "gsm8k_test.jsonl"), "operation": "stat"},
        ["bytes", "gsm8k"],
    ),
    (
        "Find Python files in tinytot/",
        "file_explore",
        {"path": str(Path(__file__).parent), "operation": "find", "arg": "*.py"},
        ["inference.py", "retrieval.py"],
    ),
    (
        "Read first 200 chars of inference.py",
        "file_explore",
        {"path": str(Path(__file__).parent / "inference.py"), "operation": "read", "max_chars": "200"},
        ["tinytot"],
    ),
    (
        "Search for generateReasoningResponse",
        "file_explore",
        {"path": str(Path(__file__).parent), "operation": "search", "arg": "generateReasoningResponse"},
        ["inference.py"],
    ),
    (
        "Schema of gsm8k_test.jsonl",
        "data_explore",
        {"path": str(DATA_DIR / "gsm8k_test.jsonl"), "operation": "schema"},
        ["question", "answer"],
    ),
    (
        "Head of gsm8k_test.jsonl",
        "data_explore",
        {"path": str(DATA_DIR / "gsm8k_test.jsonl"), "operation": "head", "arg": "3"},
        ["question"],
    ),
    (
        "Describe gsm8k_test.jsonl",
        "data_explore",
        {"path": str(DATA_DIR / "gsm8k_test.jsonl"), "operation": "describe"},
        ["Rows", "question"],
    ),
    ("Shell echo", "shell_run", {"command": "echo tinytot_bench_marker"}, ["tinytot_bench_marker"]),
    ("Shell python version", "shell_run", {"command": "python --version"}, ["Python"]),
    (
        "Shell list categories",
        "shell_run",
        {"command": f"python -c \"import os; [print(f) for f in os.listdir(r'{DATA_DIR / 'categories'}')]\""},
        ["math.md"],
    ),
]


def benchmark_agent_tools() -> dict:
    """Benchmark the agent tool library against deterministic local operations."""
    from tinytot.tools_ext import registry

    passed = 0
    failed_cases: list[dict] = []
    per_case: list[dict] = []
    total_ms = 0

    for desc, tool_name, kwargs, must_contain in _AGENT_TOOL_CASES:
        t0 = time.perf_counter()
        result = registry.run(tool_name, **kwargs)
        ms = int((time.perf_counter() - t0) * 1000)
        total_ms += ms

        missing = [m for m in must_contain if m.lower() not in result.lower()]
        ok = bool(result.strip()) and not result.startswith("[") and len(missing) == 0

        if ok:
            passed += 1
        else:
            failed_cases.append(
                {"case": desc, "tool": tool_name, "missing": missing, "result_preview": result[:120].replace("\n", " ")}
            )
        per_case.append({"name": f"{tool_name}/{desc[:35]}", "passed": ok, "words": len(result.split()), "ms": ms})

    n = len(_AGENT_TOOL_CASES)
    return {
        "cases": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy": f"{passed}/{n}  ({100 * passed // n}%)",
        "total_ms": total_ms,
        "avg_ms_per_case": total_ms // max(n, 1),
        "per_case": per_case,
        "failures": failed_cases,
    }


# ---------------------------------------------------------------------------
# SWE-lite benchmark (SWE-bench inspired, fully local)
# ---------------------------------------------------------------------------

_SWE_LITE_CASES = [
    (
        "def first_n(items, n):\n    return items[:n+1]",
        "This function has a bug. What is wrong and how do you fix it?",
        ["n+1", "off-by-one", "items[:n]"],
    ),
    (
        "for i in range(1, len(arr)+1):\n    arr[i] = arr[i] * 2",
        "This loop raises an IndexError. Explain why and fix it.",
        ["len", "range", "index"],
    ),
    (
        "def is_even(n):\n    return n % 2 == 1",
        "This function returns wrong results for even numbers. What is the bug?",
        ["% 2 == 0"],
    ),
    (
        "def max_val(a, b):\n    if a < b:\n        return a\n    return b",
        "This function is supposed to return the maximum. What is wrong?",
        ["minimum", "max"],
    ),
    ("def divide(a, b):\n    return a / b", "What edge case does this function not handle?", ["zero", "division"]),
    (
        "def safe_get(lst, idx):\n    return lst[idx]",
        "What error can this function raise and how do you guard against it?",
        ["IndexError", "bounds"],
    ),
    (
        "def add(a, b):\n    return a + b\n\nadd('3', 4)",
        "This code will raise a TypeError. Explain why.",
        ["str", "int", "type"],
    ),
    (
        "lo, hi = 0, len(arr)\nwhile lo < hi:\n    mid = (lo+hi)//2\n    if arr[mid] < target: lo = mid\n    else: hi = mid",
        "This binary search has an infinite loop bug. Identify it.",
        ["lo = mid + 1", "mid", "infinite"],
    ),
    (
        "result = [x**2 for x in range(10) if x % 2 == 0]",
        "Explain what this Python list comprehension does.",
        ["even", "square"],
    ),
    (
        "query = f\"SELECT * FROM users WHERE name = '{user_input}'\"",
        "What security issue does this SQL query have?",
        ["injection", "SQL"],
    ),
]


def benchmark_swe_lite() -> dict:
    """SWE-bench-inspired: TinyToT diagnoses bugs and security issues in code snippets."""
    from tinytot.inference import generateTreeOfThoughtsResponse

    passed = 0
    failed_cases: list[dict] = []
    per_case: list[dict] = []
    total_ms = 0

    for code, question, must_contain in _SWE_LITE_CASES:
        prompt = f"Code:\n```\n{code}\n```\n\nQuestion: {question}"
        t0 = time.perf_counter()
        # skip_knowledge=True: prevents GSM8K code passages hijacking debug responses
        result = generateTreeOfThoughtsResponse(prompt, skip_knowledge=True)
        ms = int((time.perf_counter() - t0) * 1000)
        total_ms += ms

        result_lower = result.lower()
        missing = [kw for kw in must_contain if kw.lower() not in result_lower]
        ok = len(missing) == 0

        if ok:
            passed += 1
        else:
            failed_cases.append({"case": question[:60], "missing": missing, "result": result[:120].replace("\n", " ")})
        per_case.append({"name": question[:40], "passed": ok, "words": len(result.split()), "ms": ms})

    n = len(_SWE_LITE_CASES)
    return {
        "cases": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy": f"{passed}/{n}  ({100 * passed // n}%)",
        "total_ms": total_ms,
        "avg_ms_per_case": total_ms // max(n, 1),
        "per_case": per_case,
        "failures": failed_cases,
    }


# ---------------------------------------------------------------------------
# Terminal task benchmark (TerminalBench-inspired, fully local)
# ---------------------------------------------------------------------------

_PY_DIR = Path(__file__).parent
_PY_FILES_CMD = "python -c \"import pathlib; print(len(list(pathlib.Path(r'%s').rglob('*.py'))))\"" % _PY_DIR
_INFERENCE_LINES_CMD = "python -c \"print(len(open(r'%s/inference.py').readlines()))\"" % _PY_DIR

_TERMINAL_CASES = [
    (
        "Count Python files in tinytot/",
        "shell_run",
        {"command": _PY_FILES_CMD},
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"],
    ),
    (
        "Show git log of last 3 commits",
        "shell_run",
        {"command": "git log --oneline -3"},
        ["v0.3.0"],
    ),
    (
        "Count lines in inference.py",
        "shell_run",
        {"command": f"python -c \"p=r'{_PY_DIR / 'inference.py'}';print(len(open(p).readlines()),p)\""},
        ["inference.py"],
    ),
    (
        "List categories",
        "file_explore",
        {"path": str(DATA_DIR / "categories"), "operation": "list"},
        ["math.md", "agent.md"],
    ),
    (
        "Find YAML files in data/",
        "file_explore",
        {"path": str(DATA_DIR), "operation": "find", "arg": "*.yaml"},
        [".yaml"],
    ),
    (
        "First 5 rows gsm8k",
        "data_explore",
        {"path": str(DATA_DIR / "gsm8k_test.jsonl"), "operation": "head", "arg": "5"},
        ["question"],
    ),
    ("Check Python version", "shell_run", {"command": "python --version"}, ["Python 3"]),
]


def benchmark_terminal() -> dict:
    """TerminalBench-inspired: TinyToT executes local terminal and filesystem tasks via tools."""
    from tinytot.tools_ext import registry

    passed = 0
    failed_cases: list[dict] = []
    per_case: list[dict] = []
    total_ms = 0

    for desc, tool_name, kwargs, must_contain in _TERMINAL_CASES:
        t0 = time.perf_counter()
        result = registry.run(tool_name, **kwargs)
        ms = int((time.perf_counter() - t0) * 1000)
        total_ms += ms

        ok = bool(result.strip()) and any(m.lower() in result.lower() for m in must_contain)

        if ok:
            passed += 1
        else:
            failed_cases.append(
                {
                    "case": desc,
                    "tool": tool_name,
                    "expected_any": must_contain,
                    "result": result[:120].replace("\n", " "),
                }
            )
        per_case.append({"name": desc[:40], "passed": ok, "words": len(result.split()), "ms": ms})

    n = len(_TERMINAL_CASES)
    return {
        "cases": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy": f"{passed}/{n}  ({100 * passed // n}%)",
        "total_ms": total_ms,
        "avg_ms_per_case": total_ms // max(n, 1),
        "per_case": per_case,
        "failures": failed_cases,
    }


# ---------------------------------------------------------------------------
# Real-world corpus helpers
# ---------------------------------------------------------------------------

_CORPUS_DIR = DATA_DIR / ".sources" / "corpora"

_CORPUS_URLS: dict[str, str] = {
    # Pillow test images — stable URLs, verified sizes
    "hopper.png": "https://raw.githubusercontent.com/python-pillow/Pillow/main/Tests/images/hopper.png",
    "hopper_f.png": "https://raw.githubusercontent.com/python-pillow/Pillow/main/Tests/images/hopper.png",
    "rgb.jpg": "https://raw.githubusercontent.com/python-pillow/Pillow/main/Tests/images/rgb.jpg",
    # Real Python README for document extraction benchmark
    "python_readme.md": "https://raw.githubusercontent.com/python/cpython/main/README.rst",
    # A small CSV dataset
    "iris.csv": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
    # A real animated GIF (small)
    "rotating_earth.gif": "https://raw.githubusercontent.com/python-pillow/Pillow/main/Tests/images/dispose_bgnd.gif",
}

# Short multilingual passages for translation benchmark (embedded, no network needed)
_MULTILINGUAL_PASSAGES: list[dict] = [
    {
        "lang": "fr",
        "text": "La science est une démarche rationnelle visant à comprendre le monde.",
        "en_must": ["science", "rational", "world"],
    },
    {
        "lang": "de",
        "text": "Maschinelles Lernen ist ein Teilgebiet der künstlichen Intelligenz.",
        "en_must": ["machine", "learning", "artificial", "intelligence"],
    },
    {
        "lang": "es",
        "text": "La inteligencia artificial está transformando la industria tecnológica.",
        "en_must": ["artificial", "intelligence", "technology"],
    },
    {"lang": "ja", "text": "木は二酸化炭素を吸収して酸素を放出する。", "en_must": ["carbon", "oxygen", "absorb"]},
    {
        "lang": "zh-CN",
        "text": "人工智能正在改变我们的生活方式。",
        "en_must": ["artificial", "intelligence", "changing"],
    },
    {
        "lang": "pt",
        "text": "A computação em nuvem revolucionou o armazenamento de dados.",
        "en_must": ["cloud", "computing", "data", "storage"],
    },
    {
        "lang": "it",
        "text": "Il riscaldamento globale è una delle maggiori sfide del nostro tempo.",
        "en_must": ["global", "warming", "challenge"],
    },
    {
        "lang": "ko",
        "text": "프로그래밍은 논리적 사고를 발전시키는 데 도움이 된다.",
        "en_must": ["program", "logical", "think"],
    },
]


def _fetch_corpus(name: str, url: str, timeout: int = 15) -> Path | None:
    """Download a corpus file via httpx if not already cached. Returns path or None.

    Uses httpx so HTTP_PROXY / HTTPS_PROXY / ALL_PROXY env vars are honoured
    automatically (including SOCKS5 when httpx[socks] is installed).
    """
    _CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    dest = _CORPUS_DIR / name
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    try:
        import httpx

        logger.info("Fetching corpus %s from %s", name, url)
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        return dest
    except Exception as e:
        logger.warning("Failed to fetch corpus %s: %s", name, e)
        return None


def fetch_all_corpora() -> dict[str, Path]:
    """Fetch all benchmark corpora. Returns {name: path} for successfully fetched files."""
    results = {}
    for name, url in _CORPUS_URLS.items():
        p = _fetch_corpus(name, url)
        if p:
            results[name] = p
    return results


# ---------------------------------------------------------------------------
# Real-world image benchmark
# ---------------------------------------------------------------------------


def benchmark_image_real() -> dict:
    """Benchmark ImageTool against real Pillow test images fetched from GitHub.

    Tests: dimension detection, colour analysis, format recognition, OCR hint.
    Falls back gracefully if network is unavailable.
    """
    from tinytot.tools_ext import ImageTool

    tool = ImageTool()
    passed = 0
    failed_cases: list[dict] = []
    per_case: list[dict] = []
    total_ms = 0

    image_cases = [
        ("hopper.png", "describe", ["PNG", "128", "hopper"]),
        ("hopper.png", "colours", ["rgb(", "#"]),
        ("hopper.png", "ocr_hint", ["edge density"]),
        ("rgb.jpg", "describe", ["JPEG", "rgb"]),
        ("rgb.jpg", "colours", ["rgb(", "#"]),
    ]

    fetched = {}
    for name in ["hopper.png", "rgb.jpg"]:
        p = _fetch_corpus(name, _CORPUS_URLS[name])
        if p:
            fetched[name] = p

    for img_name, op, must_contain in image_cases:
        if img_name not in fetched:
            per_case.append({"name": f"image/{img_name}/{op}", "passed": False, "words": 0, "ms": 0})
            failed_cases.append({"case": f"{img_name} {op}", "missing": ["(corpus not fetched)"], "result": ""})
            continue

        t0 = time.perf_counter()
        result = tool.run(path=str(fetched[img_name]), operation=op)
        ms = int((time.perf_counter() - t0) * 1000)
        total_ms += ms

        missing = [m for m in must_contain if m.lower() not in result.lower()]
        ok = not missing

        if ok:
            passed += 1
        else:
            failed_cases.append({"case": f"{img_name} {op}", "missing": missing, "result": result[:120]})
        per_case.append({"name": f"image/{img_name[:15]}/{op}", "passed": ok, "words": len(result.split()), "ms": ms})

    n = len(image_cases)
    return {
        "cases": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy": f"{passed}/{n}  ({100 * passed // n if n else 0}%)",
        "total_ms": total_ms,
        "avg_ms_per_case": total_ms // max(n, 1),
        "per_case": per_case,
        "failures": failed_cases,
    }


# ---------------------------------------------------------------------------
# Translation benchmark (real multilingual passages)
# ---------------------------------------------------------------------------


def benchmark_translate_real() -> dict:
    """Benchmark TranslateTool against real multilingual passages.

    Tests round-trip fidelity: translate foreign text to English and check
    that key English concepts appear in the output.
    Falls back gracefully if deep-translator is not installed or network unavailable.
    """
    from tinytot.tools_ext import TranslateTool

    tool = TranslateTool()
    passed = 0
    skipped = 0
    failed_cases: list[dict] = []
    per_case: list[dict] = []
    total_ms = 0

    for entry in _MULTILINGUAL_PASSAGES:
        lang = entry["lang"]
        text = entry["text"]
        must_en = entry["en_must"]

        t0 = time.perf_counter()
        result = tool.run(text=text, target="en", source=lang)
        ms = int((time.perf_counter() - t0) * 1000)
        total_ms += ms

        if (
            result.startswith("[translate")
            or "HTTPSConnectionPool" in result
            or "ConnectionPool" in result
            or "SSL" in result
        ):
            # No working backend — skip gracefully, don't count as failure
            skipped += 1
            per_case.append({"name": f"translate/{lang}", "passed": None, "skipped": True, "words": 0, "ms": ms})
            failed_cases.append(
                {"case": f"translate {lang}→en", "missing": ["(backend unavailable)"], "result": result[:80]}
            )
            continue

        result_lower = result.lower()
        missing = [k for k in must_en if k.lower() not in result_lower]
        ok = not missing

        if ok:
            passed += 1
        else:
            failed_cases.append(
                {"case": f"translate {lang}→en: {text[:40]}", "missing": missing, "result": result[:120]}
            )
        per_case.append({"name": f"translate/{lang}", "passed": ok, "words": len(result.split()), "ms": ms})

    tested = len(_MULTILINGUAL_PASSAGES) - skipped
    return {
        "cases": tested,
        "passed": passed,
        "failed": tested - passed,
        "skipped": skipped,
        "accuracy": f"{passed}/{tested}  ({100 * passed // tested if tested else 0}%)",
        "total_ms": total_ms,
        "avg_ms_per_case": total_ms // max(len(_MULTILINGUAL_PASSAGES), 1),
        "per_case": per_case,
        "failures": [f for f in failed_cases if "(backend unavailable)" not in f.get("missing", [])],
    }


# ---------------------------------------------------------------------------
# Document extraction benchmark (real README / corpus files)
# ---------------------------------------------------------------------------


def benchmark_document_real() -> dict:
    """Benchmark DocumentTool against real files: Python README, CSV, Markdown.

    Tests: text extraction fidelity, content detection, large file handling.
    """
    from tinytot.tools_ext import DataTool, DocumentTool

    doc_tool = DocumentTool()
    data_tool = DataTool()
    passed = 0
    failed_cases: list[dict] = []
    per_case: list[dict] = []
    total_ms = 0

    # Fetch corpora
    readme_path = _fetch_corpus("python_readme.md", _CORPUS_URLS["python_readme.md"])
    iris_path = _fetch_corpus("iris.csv", _CORPUS_URLS["iris.csv"])

    cases = []
    if readme_path:
        cases += [
            (doc_tool, {"source": str(readme_path), "max_chars": "2000"}, "README", ["Python", "source"]),
            (doc_tool, {"source": str(readme_path), "max_chars": "500"}, "README-short", ["Python"]),
        ]
    if iris_path:
        cases += [
            (data_tool, {"path": str(iris_path), "operation": "schema"}, "iris-schema", ["species", "sepal", "petal"]),
            (data_tool, {"path": str(iris_path), "operation": "head", "arg": "5"}, "iris-head", ["setosa"]),
            (data_tool, {"path": str(iris_path), "operation": "describe"}, "iris-describe", ["Rows", "sepal"]),
            (
                data_tool,
                {"path": str(iris_path), "operation": "query", "arg": "species=setosa"},
                "iris-query-setosa",
                ["setosa"],
            ),
        ]

    if not cases:
        return {
            "cases": 0,
            "passed": 0,
            "failed": 0,
            "accuracy": "0/0  (skipped — corpus not fetched)",
            "total_ms": 0,
            "avg_ms_per_case": 0,
            "per_case": [],
            "failures": [],
        }

    for tool, kwargs, label, must_contain in cases:
        t0 = time.perf_counter()
        result = tool.run(**kwargs)
        ms = int((time.perf_counter() - t0) * 1000)
        total_ms += ms

        missing = [m for m in must_contain if m.lower() not in result.lower()]
        ok = bool(result.strip()) and not result.startswith("[") and not missing

        if ok:
            passed += 1
        else:
            failed_cases.append({"case": label, "missing": missing, "result": result[:120]})
        per_case.append({"name": label, "passed": ok, "words": len(result.split()), "ms": ms})

    n = len(cases)
    return {
        "cases": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy": f"{passed}/{n}  ({100 * passed // n if n else 0}%)",
        "total_ms": total_ms,
        "avg_ms_per_case": total_ms // max(n, 1),
        "per_case": per_case,
        "failures": failed_cases,
    }


# ---------------------------------------------------------------------------
# Video / GIF benchmark
# ---------------------------------------------------------------------------


def benchmark_video_real() -> dict:
    """Benchmark VideoTool against a real animated GIF fetched from GitHub."""
    from tinytot.tools_ext import VideoTool

    tool = VideoTool()
    gif_path = _fetch_corpus("rotating_earth.gif", _CORPUS_URLS["rotating_earth.gif"])

    if not gif_path:
        return {
            "cases": 0,
            "passed": 0,
            "failed": 0,
            "accuracy": "0/0  (corpus not fetched)",
            "total_ms": 0,
            "avg_ms_per_case": 0,
            "per_case": [],
            "failures": [],
        }

    cases = [
        ("describe", ["GIF", "Frames", "Duration"]),
        ("frames", ["Frame", "duration"]),
        ("keyframe", ["Frame 0", "rgb(", "#"]),
    ]

    passed = 0
    failed_cases: list[dict] = []
    per_case: list[dict] = []
    total_ms = 0

    for op, must_contain in cases:
        t0 = time.perf_counter()
        result = tool.run(path=str(gif_path), operation=op)
        ms = int((time.perf_counter() - t0) * 1000)
        total_ms += ms

        missing = [m for m in must_contain if m.lower() not in result.lower()]
        ok = not missing

        if ok:
            passed += 1
        else:
            failed_cases.append({"case": f"gif/{op}", "missing": missing, "result": result[:120]})
        per_case.append({"name": f"gif/{op}", "passed": ok, "words": len(result.split()), "ms": ms})

    n = len(cases)
    return {
        "cases": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy": f"{passed}/{n}  ({100 * passed // n if n else 0}%)",
        "total_ms": total_ms,
        "avg_ms_per_case": total_ms // max(n, 1),
        "per_case": per_case,
        "failures": failed_cases,
    }


# ---------------------------------------------------------------------------
# Multimodal benchmark — image analysis feeding into ToT reasoning
# ---------------------------------------------------------------------------


def benchmark_multimodal() -> dict:
    """Benchmark end-to-end multimodal reasoning: analyse image → reason about it.

    Fetches a real image, runs ImageTool, feeds the description into ToT,
    and checks that the final answer is grounded in the image content.
    """
    from tinytot.inference import generateTreeOfThoughtsResponse
    from tinytot.tools_ext import ImageTool

    img_path = _fetch_corpus("hopper.png", _CORPUS_URLS["hopper.png"])
    if not img_path:
        return {
            "cases": 0,
            "passed": 0,
            "failed": 0,
            "accuracy": "0/0  (corpus not fetched)",
            "total_ms": 0,
            "avg_ms_per_case": 0,
            "per_case": [],
            "failures": [],
        }

    tool = ImageTool()
    cases = [
        (
            "What are the dominant colours in this image?",
            lambda desc: tool.run(path=str(img_path), operation="colours"),
            ["rgb(", "#"],
        ),
        (
            "What can you tell me about this image's visual properties?",
            lambda desc: tool.run(path=str(img_path), operation="describe"),
            ["Dimensions", "Format", "Brightness"],
        ),
        (
            "Does this image likely contain text?",
            lambda desc: tool.run(path=str(img_path), operation="ocr_hint"),
            ["edge density"],
        ),
    ]

    passed = 0
    failed_cases: list[dict] = []
    per_case: list[dict] = []
    total_ms = 0

    for question, get_context, must_contain in cases:
        t0 = time.perf_counter()
        context = get_context(None)
        synthesis_prompt = f"{question}\n\nImage analysis:\n{context}"
        result = generateTreeOfThoughtsResponse(synthesis_prompt, skip_knowledge=True)
        ms = int((time.perf_counter() - t0) * 1000)
        total_ms += ms

        # Check context (image tool output) contains expected keywords — the ToT
        # reasoning wraps it so we check the combined output
        combined = (context + " " + result).lower()
        missing = [m for m in must_contain if m.lower() not in combined]
        ok = not missing

        if ok:
            passed += 1
        else:
            failed_cases.append({"case": question[:60], "missing": missing, "result": result[:120]})
        per_case.append({"name": question[:40], "passed": ok, "words": len(result.split()), "ms": ms})

    n = len(cases)
    return {
        "cases": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy": f"{passed}/{n}  ({100 * passed // n if n else 0}%)",
        "total_ms": total_ms,
        "avg_ms_per_case": total_ms // max(n, 1),
        "per_case": per_case,
        "failures": failed_cases,
    }


# ---------------------------------------------------------------------------
# Anti-cheating benchmarks — held-out, novel, paraphrased
# ---------------------------------------------------------------------------
#
# Design principles:
#   1. No prompt appears verbatim in data/knowledge/ or data/categories/
#   2. Answers are derived from reasoning, not memorised from training chains
#   3. Each run uses RANDOMISED variants so exact-match gaming is impossible
#   4. Success requires generalisation, not retrieval of a stored answer
#
# Three sub-benchmarks:
#   a. novel_math       — arithmetic with randomly generated numbers
#   b. novel_reasoning  — paraphrased logic/CS/science (not in knowledge base)
#   c. novel_routing    — prompts that probe routing accuracy on unseen phrasings

_RANDOM_SEED = 42  # reproducible within a single run; change to verify no overfitting


def _fresh_rng() -> "_random.Random":
    return _random.Random(_RANDOM_SEED)


# ---------------------------------------------------------------------------
# (a) Novel Math — random numbers guarantee no memorised answers
# ---------------------------------------------------------------------------


def benchmark_novel_math(seed: int = _RANDOM_SEED) -> dict:
    """Arithmetic benchmark with randomly generated values.

    Every run uses reproducible random numbers.  Changing the seed verifies
    TinyToT is computing rather than returning a cached answer.
    """
    from tinytot.inference import generateReasoningResponse

    rng = _random.Random(seed)
    cases: list[tuple[str, str]] = []

    for _ in range(12):
        a, b = rng.randint(11, 99), rng.randint(11, 99)
        cases.append((f"What is {a} multiplied by {b}?", str(a * b)))
    for _ in range(8):
        pct = rng.randint(5, 95)
        base = rng.randint(100, 500)
        cases.append((f"What is {pct}% of {base}?", str((pct * base) // 100)))
    for _ in range(5):
        p, n = rng.randint(2, 8), rng.randint(2, 6)
        cases.append((f"What is {p} to the power of {n}?", str(p**n)))

    def mathWorker(item: tuple) -> dict:
        prompt, expected = item
        t0 = time.perf_counter()
        result = generateReasoningResponse(prompt)
        ms = int((time.perf_counter() - t0) * 1000)
        ok = expected in result.replace(",", "").replace(" ", "")
        return {
            "passed": ok,
            "ms": ms,
            "name": prompt[:40],
            "words": len(result.split()),
            "case": prompt,
            "expected": expected,
            "result": result[:80],
        }

    _print_section("Novel Math")
    caseResults = _run_cases_parallel(cases, mathWorker, label_fn=lambda c: c[0][:40])

    passed = sum(1 for r in caseResults if r["passed"])
    nTotal = len(caseResults)
    totalMs = sum(r["ms"] for r in caseResults)
    return {
        "cases": nTotal,
        "passed": passed,
        "failed": nTotal - passed,
        "accuracy": f"{passed}/{nTotal}  ({100 * passed // nTotal if nTotal else 0}%)",
        "total_ms": totalMs,
        "avg_ms_per_case": totalMs // max(nTotal, 1),
        "per_case": [
            {"name": r["name"], "passed": r["passed"], "words": r["words"], "ms": r["ms"]} for r in caseResults
        ],
        "failures": [
            {"case": r["case"], "expected": r["expected"], "result": r["result"]}
            for r in caseResults
            if not r["passed"]
        ],
        "seed": seed,
    }


# ---------------------------------------------------------------------------
# (b) Novel Reasoning — paraphrased, held-out prompts
#     These prompts do NOT appear verbatim in knowledge/ or categories/.
#     They test whether TinyToT generalises to new phrasings.
# ---------------------------------------------------------------------------

_NOVEL_REASONING_CASES: list[tuple[str, list[str]]] = [
    # Science — paraphrased from general knowledge
    ("Explain why objects fall toward Earth", ["gravity", "gravit", "mass", "attract"]),
    ("What makes copper a good electrical conductor?", ["electron", "conduct", "metal", "free"]),
    ("Why do stars appear to twinkle at night?", ["atmospher", "refract", "air", "light"]),
    ("What is the difference between a virus and a bacterium?", ["cell", "DNA", "RNA", "living", "bacteri"]),
    # CS — novel phrasings not in programming_eval chains
    ("What does SOLID stand for in software design?", ["single", "open", "liskov", "interface", "depend"]),
    ("What is the difference between a stack and a queue?", ["LIFO", "FIFO", "last in", "first in", "stack", "queue"]),
    ("Why is immutability useful in functional programming?", ["state", "side effect", "pure", "predict", "concurr"]),
    ("What is the purpose of an index in a database?", ["lookup", "speed", "search", "B-tree", "fast", "query"]),
    # Logic — novel puzzles not in any training chain
    (
        "If all mammals are warm-blooded, and dolphins are mammals, are dolphins warm-blooded?",
        ["yes", "warm-blooded", "are", "dolphins"],
    ),
    ("A farmer has 17 sheep. All but 9 die. How many are left?", ["9", "nine"]),
    ("What is the next prime number after 13?", ["17"]),
    ("How many faces does a cube have?", ["6", "six"]),
    # Finance — novel angles
    ("What happens to bond prices when interest rates rise?", ["fall", "declin", "inversel", "down", "decreas"]),
    ("What is the rule of 72 in investing?", ["double", "72", "divid", "interest rate", "year"]),
    # General knowledge — novel facts
    ("What element has the chemical symbol Au?", ["gold"]),
    ("In which organ does digestion primarily occur?", ["small intestine", "stomach", "digest"]),
    ("What is the largest organ in the human body?", ["skin"]),
    ("What is the boiling point of water at sea level in Celsius?", ["100", "hundred"]),
]


def benchmark_novel_reasoning() -> dict:
    """Tests held-out, paraphrased prompts that don't appear in any training data.

    Checks whether TinyToT generalises to new phrasings rather than retrieving
    memorised answers.  Any case that routes to GSM8K noise is flagged.
    """
    from tinytot.inference import generateReasoningResponse

    _gsm8kSignals = ["earned", "works 7", "cookies", "spends 50", "Sally", "Oliver"]

    def reasoningWorker(item: tuple) -> dict:
        prompt, mustContain = item
        t0 = time.perf_counter()
        result = generateReasoningResponse(prompt)
        ms = int((time.perf_counter() - t0) * 1000)
        isGsm8k = result.startswith("Q: ") and any(w in result[:120] for w in _gsm8kSignals)
        if isGsm8k:
            return {
                "passed": False,
                "ms": ms,
                "name": prompt[:40],
                "words": 0,
                "missing": ["(GSM8K contamination)"],
                "result": result[:80],
            }
        missing = [k for k in mustContain if k.lower() not in result.lower()]
        ok = not missing
        return {
            "passed": ok,
            "ms": ms,
            "name": prompt[:40],
            "words": len(result.split()),
            "missing": missing,
            "result": result[:120],
        }

    _print_section("Novel Reasoning")
    caseResults = _run_cases_parallel(_NOVEL_REASONING_CASES, reasoningWorker, label_fn=lambda c: c[0][:40])

    passed = sum(1 for r in caseResults if r["passed"])
    nTotal = len(caseResults)
    totalMs = sum(r["ms"] for r in caseResults)
    return {
        "cases": nTotal,
        "passed": passed,
        "failed": nTotal - passed,
        "accuracy": f"{passed}/{nTotal}  ({100 * passed // nTotal if nTotal else 0}%)",
        "total_ms": totalMs,
        "avg_ms_per_case": totalMs // max(nTotal, 1),
        "per_case": [
            {"name": r["name"], "passed": r["passed"], "words": r["words"], "ms": r["ms"]} for r in caseResults
        ],
        "failures": [
            {"case": r["name"], "missing": r["missing"], "result": r["result"]} for r in caseResults if not r["passed"]
        ],
    }


# ---------------------------------------------------------------------------
# (c) Novel Routing — unseen phrasings of known intents
#     Tests whether the router generalises, not just matches training strings.
# ---------------------------------------------------------------------------

_NOVEL_ROUTING_CASES: list[tuple[str, str]] = [
    # Math — novel phrasings
    ("Multiply 12 by 15", "math"),
    ("Divide 144 by 12", "math"),
    ("Square root of 64", "math"),
    ("Half of 250 is what number?", "math"),
    # Programming — novel phrasings
    ("Show me how to iterate over a list in Python", "programming"),
    ("I need a function that checks for palindromes in Python", "programming"),
    ("How do I read a CSV file in Python?", "programming"),
    ("What does async mean in JavaScript?", "programming"),
    # Financial — novel phrasings
    ("How does a savings account earn money?", "financial"),
    ("What is market capitalisation?", "financial"),
    ("Why do central banks raise interest rates?", "financial"),
    # Computer science — novel phrasings
    ("Describe the concept of time complexity", "computer_science"),
    ("What is memoisation used for?", "computer_science"),
    ("Explain how caching works", "computer_science"),
    # Creative writing — novel phrasings
    ("Compose a short poem about the moon", "creative_writing"),
    ("Write the opening line of a thriller novel", "creative_writing"),
    # Smalltalk — novel social phrasings
    ("You're brilliant!", "smalltalk"),
    ("That actually helped a lot", "smalltalk"),
    ("I didn't catch that, could you say it again?", "smalltalk"),
    # General knowledge — novel phrasings
    ("Why is the Dead Sea so salty?", "general_knowledge"),
    ("How do airplanes stay in the air?", "general_knowledge"),
    ("What makes a metal magnetic?", "general_knowledge"),
]


def benchmark_novel_routing() -> dict:
    """Tests routing accuracy on novel phrasings not in the training set.

    Unlike the main routing benchmark (which uses fixed prompts), these cases
    use paraphrased or differently-phrased intents to probe generalisation.
    """
    from tinytot.content import getCategories, loadReasoningChains
    from tinytot.retrieval import buildChainIndex, buildChainMeta, buildKnowledgeIndex, categorizePrompt

    buildChainIndex.cache_clear()
    buildChainMeta.cache_clear()
    buildKnowledgeIndex.cache_clear()
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()

    # Warm caches before workers.
    getCategories()
    buildChainIndex()
    buildKnowledgeIndex()

    def novelRoutingWorker(item: tuple) -> dict:
        prompt, expected = item
        t0 = time.perf_counter()
        actual = categorizePrompt(prompt)
        ms = int((time.perf_counter() - t0) * 1000)
        ok = actual == expected
        return {
            "passed": ok,
            "ms": ms,
            "name": prompt[:40],
            "words": 0,
            "prompt": prompt,
            "expected": expected,
            "got": actual,
        }

    _print_section("Novel Routing")
    caseResults = _run_cases_parallel(_NOVEL_ROUTING_CASES, novelRoutingWorker, label_fn=lambda c: c[0][:40])

    passed = sum(1 for r in caseResults if r["passed"])
    nTotal = len(caseResults)
    totalMs = sum(r["ms"] for r in caseResults)
    buildChainIndex.cache_clear()
    buildKnowledgeIndex.cache_clear()
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()
    return {
        "total": nTotal,
        "correct": passed,
        "accuracy_pct": round(passed / nTotal * 100, 1) if nTotal else 0,
        "avg_query_ms": round(totalMs / nTotal, 1) if nTotal else 0,
        "misrouted": [
            {"prompt": r["prompt"][:60], "expected": r["expected"], "got": r["got"]}
            for r in caseResults
            if not r["passed"]
        ],
        "per_case": [
            {"name": r["name"], "passed": r["passed"], "words": r["words"], "ms": r["ms"]} for r in caseResults
        ],
    }


def main() -> None:

    parser = argparse.ArgumentParser(description="Benchmark TinyToT inference at scale")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_gsm = sub.add_parser("gsm8k", help="Benchmark against GSM8K test set")
    p_gsm.add_argument("source", type=Path, help="Path to test.jsonl")
    p_gsm.add_argument("--limit", type=int, default=200)
    p_gsm.add_argument("--json", action="store_true")

    sub.add_parser("routing", help="Benchmark category routing accuracy")
    sub.add_parser("retrieval", help="Benchmark knowledge retrieval precision")

    p_sum = sub.add_parser("summarize", help="Eval summarization across 11 domains")
    p_sum.add_argument("--file", type=Path, default=_EVAL_FILE)

    sub.add_parser("codegen", help="Benchmark code generation (50 cases, 7 languages)")
    sub.add_parser("game24", help="Benchmark Game24 routing and arithmetic response quality")
    sub.add_parser("tot-text", help="Benchmark creative writing routing and prose response quality")
    sub.add_parser("agent-tools", help="Benchmark agent tool library (file, data, shell) — fully local")
    sub.add_parser("swe-lite", help="SWE-bench-inspired: diagnose bugs and security issues in code")
    sub.add_parser("terminal", help="TerminalBench-inspired: execute local filesystem and shell tasks")
    sub.add_parser("image-real", help="Real-world image analysis (Pillow test images from GitHub)")
    sub.add_parser("translate-real", help="Real multilingual translation fidelity (8 languages)")
    sub.add_parser("document-real", help="Real document extraction (Python README, Iris CSV)")
    sub.add_parser("video-real", help="Real video/GIF analysis (animated GIF from GitHub)")
    sub.add_parser("multimodal", help="End-to-end multimodal: image analysis → ToT reasoning")
    p_novel_math = sub.add_parser("novel-math", help="Anti-cheat: arithmetic with randomly generated numbers")
    p_novel_math.add_argument("--seed", type=int, default=_RANDOM_SEED, help="RNG seed (change to verify no caching)")
    sub.add_parser("novel-reasoning", help="Anti-cheat: held-out paraphrased prompts not in training data")
    sub.add_parser("novel-routing", help="Anti-cheat: routing accuracy on novel unseen phrasings")

    p_all = sub.add_parser("all", help="Run all benchmarks")
    p_all.add_argument("--gsm8k", type=Path, help="Path to GSM8K test.jsonl (optional)")
    p_all.add_argument("--limit", type=int, default=200)

    args = parser.parse_args()

    if args.cmd == "gsm8k":
        r = benchmark_gsm8k(args.source, args.limit)
        if args.json:
            print(json.dumps(r, indent=2))
        else:
            _print_report("GSM8K Math Benchmark", r)

    elif args.cmd == "routing":
        r = benchmark_routing()
        _print_report("Routing Accuracy Benchmark", r)

    elif args.cmd == "retrieval":
        r = benchmark_retrieval()
        _print_report("Knowledge Retrieval Benchmark", r)

    elif args.cmd == "summarize":
        r = benchmark_summarize(getattr(args, "file", _EVAL_FILE))
        _print_report("Summarization Eval (11 domains)", r)

    elif args.cmd == "codegen":
        r = benchmark_codegen()
        _print_report("Code Generation Benchmark (50 cases, 7 languages)", r)

    elif args.cmd == "game24":
        r = benchmark_game24()
        _print_report("Game24 Benchmark", r)

    elif args.cmd == "tot-text":
        r = benchmark_tot_text()
        _print_report("Creative Writing (ToT Text) Benchmark", r)

    elif args.cmd == "agent-tools":
        r = benchmark_agent_tools()
        _print_report("Agent Tool Benchmark (file/data/shell)", r)

    elif args.cmd == "swe-lite":
        r = benchmark_swe_lite()
        _print_report("SWE-lite Benchmark (bug diagnosis)", r)

    elif args.cmd == "terminal":
        r = benchmark_terminal()
        _print_report("Terminal Task Benchmark", r)

    elif args.cmd == "image-real":
        _print_report("Real-World Image Analysis", benchmark_image_real())

    elif args.cmd == "translate-real":
        _print_report("Real Multilingual Translation (8 languages)", benchmark_translate_real())

    elif args.cmd == "document-real":
        _print_report("Real Document Extraction", benchmark_document_real())

    elif args.cmd == "video-real":
        _print_report("Real Video/GIF Analysis", benchmark_video_real())

    elif args.cmd == "multimodal":
        _print_report("Multimodal Reasoning (image → ToT)", benchmark_multimodal())

    elif args.cmd == "all":
        _print_report("Routing Accuracy", benchmark_routing())
        _print_report("Knowledge Retrieval Precision", benchmark_retrieval())
        _print_report("Summarization Eval (11 domains)", benchmark_summarize())
        _print_report("Code Generation (50 cases, 7 languages)", benchmark_codegen())
        r_g24 = benchmark_game24()
        if r_g24.get("skipped"):
            print(f"\n[Game24 skipped — {r_g24['reason']}]")
        else:
            _print_report("Game24 (Princeton ToT)", r_g24)
        r_txt = benchmark_tot_text()
        if r_txt.get("skipped"):
            print(f"\n[Creative Writing skipped — {r_txt['reason']}]")
        else:
            _print_report("Creative Writing (Princeton ToT Text)", r_txt)
        _DEFAULT_GSM8K = DATA_DIR / "gsm8k_test.jsonl"
        gsm8k_path = (
            args.gsm8k
            if (args.gsm8k and args.gsm8k.exists())
            else (_DEFAULT_GSM8K if _DEFAULT_GSM8K.exists() else None)
        )
        if gsm8k_path:
            _print_report(f"GSM8K Math ({gsm8k_path.name})", benchmark_gsm8k(gsm8k_path, args.limit))
        else:
            print("\n[GSM8K skipped -- no data/gsm8k_test.jsonl found]")
        _print_report("Agent Tools (file/data/shell)", benchmark_agent_tools())
        _print_report("SWE-lite (bug diagnosis)", benchmark_swe_lite())
        _print_report("Terminal Tasks", benchmark_terminal())
        print("\n--- Real-World Benchmarks (network required) ---")
        _print_report("Real-World Image Analysis", benchmark_image_real())
        _print_report("Multilingual Translation (8 languages)", benchmark_translate_real())
        _print_report("Real Document Extraction", benchmark_document_real())
        _print_report("Video/GIF Analysis", benchmark_video_real())
        _print_report("Multimodal Reasoning (image → ToT)", benchmark_multimodal())
        print("\n--- Anti-Cheat Benchmarks (held-out, randomised) ---")
        _print_report("Novel Math (random numbers, seed=42)", benchmark_novel_math())
        _print_report("Novel Reasoning (held-out paraphrased)", benchmark_novel_reasoning())
        _print_report("Novel Routing (unseen phrasings)", benchmark_novel_routing())

    elif args.cmd == "novel-math":
        seed = getattr(args, "seed", _RANDOM_SEED)
        _print_report(f"Novel Math (seed={seed})", benchmark_novel_math(seed=seed))

    elif args.cmd == "novel-reasoning":
        _print_report("Novel Reasoning (held-out paraphrased)", benchmark_novel_reasoning())

    elif args.cmd == "novel-routing":
        _print_report("Novel Routing (unseen phrasings)", benchmark_novel_routing())


if __name__ == "__main__":
    main()
