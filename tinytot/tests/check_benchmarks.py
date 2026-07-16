"""
tinytot.tests.check_benchmarks — Benchmark regression guard with diff reporting.

Compares current benchmark scores against a JSON baseline file
(data/benchmarks_baseline.json). Any regression from baseline is reported
in red and causes exit code 1.

No hardcoded floors — the baseline IS the floor. Update it intentionally
with --update-baseline when you accept a change.

Usage
-----
    # Run check (used by pre-commit hook):
    pipenv run python -m tinytot.tests.check_benchmarks

    # Accept current scores as the new baseline:
    pipenv run python -m tinytot.tests.check_benchmarks --update-baseline

    # Report only (no exit code change):
    pipenv run python -m tinytot.tests.check_benchmarks --report-only

Output format (pytest-style)
-----------------------------
    PASSED   routing       53/53  [= baseline]
    PASSED   retrieval     15/15  [+1 vs baseline]
    FAILED   codegen       48/49  [-1 vs baseline]  ← regression
    SKIPPED  translate_es  (no backend available)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Baseline I/O
# ---------------------------------------------------------------------------

_BASELINE_PATH = Path(__file__).parent.parent / "_data" / "benchmarks_baseline.json"


def load_baseline() -> Dict[str, int]:
    if _BASELINE_PATH.exists():
        try:
            return json.loads(_BASELINE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_baseline(scores: Dict[str, int]) -> None:
    _BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _BASELINE_PATH.write_text(
        json.dumps(scores, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Baseline updated → {_BASELINE_PATH}")


# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------

_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _c(text: str, *codes: str) -> str:
    """Apply ANSI codes when outputting to a real terminal."""
    if not (sys.stdout.isatty() or sys.stderr.isatty()):
        return text
    return "".join(codes) + text + _RESET


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def _format_result(name: str, got: int, baseline: Optional[int]) -> tuple[str, bool]:
    """Return (formatted_line, is_failure).

    Failure = score regressed below baseline.
    If no baseline exists, the run always passes (first run).
    """
    if baseline is None:
        label = _c("NEW     ", _YELLOW, _BOLD)
        return f"  {label} {name:<20} {got:>3}  (no baseline — will be saved)", False

    delta = got - baseline
    regressed = delta < 0

    if delta > 0:
        diff = _c(f"[+{delta}]", _GREEN)
        label = _c("IMPROVED", _GREEN, _BOLD)
    elif delta < 0:
        diff = _c(f"[{delta}]", _RED)
        label = _c("FAILED  ", _RED, _BOLD)
    else:
        diff = "[=]"
        label = _c("PASSED  ", _GREEN)

    line = f"  {label} {name:<20} {got:>3}  (baseline {baseline}) {diff}"
    return line, regressed


# ---------------------------------------------------------------------------
# Benchmark runners
# ---------------------------------------------------------------------------


def run_benchmarks() -> Dict[str, int]:
    """Run all fast benchmarks (core + anti-cheat) and return raw scores."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from tinytot.benchmark import (
        benchmark_codegen,
        benchmark_novel_math,
        benchmark_novel_reasoning,
        benchmark_novel_routing,
        benchmark_retrieval,
        benchmark_routing,
        benchmark_summarize,
    )
    from tinytot.codegen import _loadConfig, _loadPatterns
    from tinytot.content import getCategories, loadKnowledgePassages, loadReasoningChains
    from tinytot.retrieval import buildChainIndex, buildChainMeta, buildKnowledgeIndex

    for fn in (
        _loadPatterns,
        _loadConfig,
        buildChainIndex,
        buildChainMeta,
        buildKnowledgeIndex,
        loadKnowledgePassages,
        getCategories,
        loadReasoningChains,
    ):
        fn.cache_clear()

    suite = {
        "routing": (benchmark_routing, "correct"),
        "retrieval": (benchmark_retrieval, "hits"),
        "summarization": (benchmark_summarize, "passed"),
        "codegen": (benchmark_codegen, "passed"),
        "novel_math": (benchmark_novel_math, "passed"),
        "novel_reasoning": (benchmark_novel_reasoning, "passed"),
        "novel_routing": (benchmark_novel_routing, "correct"),
    }

    scores: Dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=len(suite)) as pool:
        futureMap = {pool.submit(fn): (name, key) for name, (fn, key) in suite.items()}
        for future in as_completed(futureMap):
            name, key = futureMap[future]
            scores[name] = future.result().get(key, 0)
    return scores


# ---------------------------------------------------------------------------
# Main check logic
# ---------------------------------------------------------------------------


def check(scores: Dict[str, int], report_only: bool = False) -> int:
    baseline = load_baseline()
    failures = []
    lines = []

    for name in sorted(scores):
        got = scores[name]
        prev = baseline.get(name)
        line, isFail = _format_result(name, got, prev)
        lines.append(line)
        if isFail:
            failures.append((name, got, prev))

    from tinytot.benchmark import _print_section

    _print_section("Benchmark Regression Report")
    for ln in lines:
        print(ln)
    print(_c("=" * 58, _RESET))

    if failures:
        print()
        for name, got, prev in failures:
            print(
                f"  {_c('REGRESSION', _RED, _BOLD)}: {name} dropped {prev} → {got}  (delta {got - prev})",
                file=sys.stderr,
            )
        print(
            "\n  Fix the regression, or run --update-baseline if intentional.\n",
            file=sys.stderr,
        )
        return 0 if report_only else 1

    print(_c("\n  All benchmarks at or above baseline.\n", _GREEN))
    return 0


def main() -> int:
    update = "--update-baseline" in sys.argv
    report = "--report-only" in sys.argv

    print("Running benchmark regression check...")
    scores = run_benchmarks()

    if update:
        save_baseline(scores)
        print("Baseline saved.")
        return 0

    exitCode = check(scores, report_only=report)

    # Auto-ratchet: if all passed and any score improved, advance baseline
    if exitCode == 0 and not report:
        current = load_baseline()
        improved = {k: v for k, v in scores.items() if v > current.get(k, -1)}
        if improved or not current:
            save_baseline({**current, **scores})
            if improved:
                print(
                    _c(
                        f"  Baseline auto-advanced: {', '.join(f'{k} → {scores[k]}' for k in improved)}",
                        _GREEN,
                    )
                )

    return exitCode


if __name__ == "__main__":
    sys.exit(main())
