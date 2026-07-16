"""
tinytot.eval_summarize -- Run the summarization eval dataset.

Reads data/eval/summarize_eval.md, runs each passage through summarizeDocument,
checks that the summary contains all must-contain phrases, and prints a report.

Usage:
    pipenv run python -m tinytot.eval_summarize
    pipenv run python -m tinytot.eval_summarize --verbose
    pipenv run python -m tinytot.eval_summarize --file path/to/other_eval.md
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

from .content import DATA_DIR
from .summarize import summarizeDocument

_DEFAULT_EVAL = DATA_DIR / "eval" / "summarize_eval.md"
_DEFAULT_MAX_WORDS = 50


def _parse_eval_file(path: Path) -> list[dict]:
    """Parse a summarize_eval.md file into a list of test cases.

    Each test case is a dict with keys:
        name        str   -- the section heading (e.g. "climate-science")
        input       str   -- the passage to summarize
        must_contain list[str] -- phrases the summary must include
        max_words   int   -- word budget for the summary
    """
    text = path.read_text(encoding="utf-8")
    cases = []

    # Split on "---\n\n## " (top-level section dividers)
    raw_sections = re.split(r"\n---\n+", text)

    for section in raw_sections:
        # Name line: "## some-name"
        name_match = re.match(r"##\s+(\S+)", section.strip())
        if not name_match:
            continue
        name = name_match.group(1)

        # Optional max_words override: "max_words: N"
        mw_match = re.search(r"max_words:\s*(\d+)", section)
        max_words = int(mw_match.group(1)) if mw_match else _DEFAULT_MAX_WORDS

        # Input block: content between "### Input\n" and next "###"
        input_match = re.search(r"### Input\n(.*?)(?=\n###|\Z)", section, re.DOTALL)
        if not input_match:
            continue
        passage = input_match.group(1).strip()

        # Must contain: bullet list under "### Must Contain"
        mc_match = re.search(r"### Must Contain\n(.*?)(?=\n###|\Z)", section, re.DOTALL)
        must_contain = []
        if mc_match:
            for line in mc_match.group(1).splitlines():
                item = line.strip().lstrip("- ").strip()
                if item:
                    must_contain.append(item)

        cases.append(
            {
                "name": name,
                "input": passage,
                "must_contain": must_contain,
                "max_words": max_words,
            }
        )

    return cases


def run_eval(path: Path = _DEFAULT_EVAL, verbose: bool = False) -> bool:
    """Run all test cases in the eval file and print a report.

    Returns True if all cases passed.
    """
    cases = _parse_eval_file(path)
    if not cases:
        print(f"No test cases found in {path}")
        return False

    passed = 0
    failed = 0
    total_ms = 0

    print(f"\nSummarization eval: {path.name}  ({len(cases)} cases)\n")
    print(f"{'Case':<30} {'Words':>5} {'ms':>5}  {'Result'}")
    print("-" * 60)

    for case in cases:
        t0 = time.time()
        summary = summarizeDocument(case["input"], max_words=case["max_words"])
        ms = int((time.time() - t0) * 1000)
        total_ms += ms

        summary_lower = summary.lower()
        missing = [p for p in case["must_contain"] if p.lower() not in summary_lower]

        if missing:
            failed += 1
            status = f"FAIL  (missing: {', '.join(missing)})"
        else:
            passed += 1
            status = "PASS"

        word_count = len(summary.split())
        print(f"{case['name']:<30} {word_count:>5} {ms:>5}  {status}")

        if verbose or missing:
            print(f"  Summary: {summary}")
            print()

    print("-" * 60)
    print(f"Result: {passed}/{len(cases)} passed  ({total_ms}ms total)\n")

    return failed == 0


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run TinyToT summarization eval")
    parser.add_argument("--file", type=Path, default=_DEFAULT_EVAL, help="Path to eval markdown file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print every summary, not just failures")
    args = parser.parse_args()

    ok = run_eval(path=args.file, verbose=args.verbose)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
