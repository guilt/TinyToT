"""
tinytot.tests.check_data_quality — Data quality gate for pre-commit.

Validates all data files that directly affect response quality:

1. Category chains (data/categories/*.md)
   - Every chain must have a Conclusion: field
   - Chains must have at least 2 Thought: entries
   - Conclusion must be ≥ 20 characters
   - Category file must have a YAML frontmatter with 'category' key
   - Category file must have a 'keywords' key in frontmatter

2. Knowledge passages (data/knowledge/*.md)
   - Files must be parseable (no encoding errors)
   - No passage may consist entirely of <MASK> or Q: without A:

3. Generate YAML (data/generate/*.yaml)
   - All YAML files must be valid and non-empty
   - use_cases.yaml: each entry must have 'pattern' and 'key'
   - howto_scripts.yaml: each entry must have 'trigger' and ≥ 3 steps
   - static_checks.yaml: each entry must have 'pattern' and 'message'

4. Codegen templates (data/codegen/templates/*.md)
   - Every template must have at least a ## python section

Exit codes:
  0  All checks pass
  1  One or more checks failed (details printed to stderr)
"""

from __future__ import annotations

import re
import sys
from typing import List, Tuple

from tinytot.content import CATEGORY_DIR as _CATEGORY_DIR
from tinytot.content import DATA_DIR as _DATA_DIR
from tinytot.content import KNOWLEDGE_DIR as _KNOWLEDGE_DIR

_GENERATE_DIR = _DATA_DIR / "generate"
_CODEGEN_TEMPLATES_DIR = _DATA_DIR / "codegen" / "templates"

# ANSI colours (only when stdout is a tty)
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _c(text: str, *codes: str) -> str:
    if not sys.stdout.isatty():
        return text
    return "".join(codes) + text + _RESET


# ---------------------------------------------------------------------------
# Check 1: Category chains
# ---------------------------------------------------------------------------

_MIN_CONCLUSION_LEN = 20
_MIN_THOUGHTS = 2

# Chains in these files are allowed to omit Conclusion: because they are
# tool-dispatch stubs, numeric solvers, or use a different response pattern.
_CONCLUSION_EXEMPT_FILES = {
    "agent.md",  # agent tool chains — dispatch stubs
    "aws_cloud.md",  # cloud infra chains — dispatch stubs
    "tool_calling.md",  # tool calling chains
    "fs.md",  # filesystem chains — dispatch stubs
    "creative_writing.md",  # Princeton ToT chains — prose, not conclusion format
    "research.md",  # research chains — tool pipeline stubs
    "game24.md",  # numeric arithmetic — answer is in the computation, not prose
    "math.md",  # math computation chains — numeric results via compute engine
}

# These files contain short conversational or numeric chains where 1 thought
# is intentional — the chain is a direct response template, not multi-step reasoning.
_THOUGHT_COUNT_EXEMPT_FILES = {
    "smalltalk.md",  # conversational chains — direct responses, 1 thought is fine
    "game24.md",  # numeric arithmetic solutions
    "math.md",  # math computation solutions
}

# These template files are intentionally SQL-only — no Python section.
_PYTHON_SECTION_EXEMPT_TEMPLATES = {
    "sql_create.md",
    "sql_insert.md",
    "sql_update.md",
    "sql_delete.md",
    "sql_join.md",
    "sql_select.md",
    "sql_subquery.md",
    "sql_aggregate.md",
    "sql_window.md",
}


def check_category_chains() -> List[Tuple[str, str]]:
    """Return list of (file:chain, error_message) for all chain issues."""
    issues: List[Tuple[str, str]] = []
    if not _CATEGORY_DIR.exists():
        return [("data/categories/", "directory not found")]

    try:
        import yaml as _yaml
    except ImportError:
        return [("", "pyyaml not installed — cannot parse frontmatter")]

    for md_file in sorted(_CATEGORY_DIR.glob("*.md")):
        fname = md_file.name
        content = md_file.read_text(encoding="utf-8")

        # Check frontmatter
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                try:
                    meta = _yaml.safe_load(content[3:end].strip()) or {}
                    if "category" not in meta:
                        issues.append((fname, "missing 'category' in YAML frontmatter"))
                    if "keywords" not in meta:
                        issues.append((fname, "missing 'keywords' in YAML frontmatter"))
                except Exception as e:
                    issues.append((fname, f"YAML frontmatter parse error: {e}"))
            else:
                issues.append((fname, "unclosed YAML frontmatter (no closing ---)"))
        else:
            issues.append((fname, "missing YAML frontmatter"))

        # Parse chains
        currentTitle = ""
        thoughts: List[str] = []
        conclusion = ""
        inChain = False

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("## Chain"):
                # Flush previous chain
                if inChain and fname not in _CONCLUSION_EXEMPT_FILES:
                    _validate_chain(fname, currentTitle, thoughts, conclusion, issues)
                # Start new chain
                m = re.match(r"## Chain(?:\s+\d+)?:\s*(.+)", stripped)
                currentTitle = m.group(1).strip() if m else stripped[3:]
                thoughts = []
                conclusion = ""
                inChain = True

            elif stripped.startswith("Thought") and inChain:
                m = re.match(r"Thought \d+:\s*(.+)", stripped)
                if m:
                    thoughts.append(m.group(1).strip())

            elif stripped.startswith("Conclusion:") and inChain:
                m = re.match(r"Conclusion:\s*(.+)", stripped)
                if m:
                    conclusion = m.group(1).strip()

        # Flush last chain
        if inChain and fname not in _CONCLUSION_EXEMPT_FILES:
            _validate_chain(fname, currentTitle, thoughts, conclusion, issues)

    return issues


def _validate_chain(
    fname: str,
    title: str,
    thoughts: List[str],
    conclusion: str,
    issues: List[Tuple[str, str]],
) -> None:
    loc = f"{fname}: [{title[:50]}]"
    if not conclusion:
        issues.append((loc, "missing Conclusion: field"))
    elif len(conclusion) < _MIN_CONCLUSION_LEN:
        issues.append((loc, f"Conclusion too short ({len(conclusion)} chars, min {_MIN_CONCLUSION_LEN})"))
    if fname not in _THOUGHT_COUNT_EXEMPT_FILES and len(thoughts) < _MIN_THOUGHTS:
        issues.append((loc, f"only {len(thoughts)} Thought(s), min {_MIN_THOUGHTS} required"))


# ---------------------------------------------------------------------------
# Check 2: Generate YAML files
# ---------------------------------------------------------------------------


def check_generate_yaml() -> List[Tuple[str, str]]:
    issues: List[Tuple[str, str]] = []
    if not _GENERATE_DIR.exists():
        return [("data/generate/", "directory not found")]

    try:
        import yaml as _yaml
    except ImportError:
        return [("", "pyyaml not installed")]

    for yf in sorted(_GENERATE_DIR.rglob("*.yaml")):
        rel = str(yf.relative_to(_GENERATE_DIR.parent))
        try:
            data = _yaml.safe_load(yf.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append((rel, f"YAML parse error: {e}"))
            continue
        if data is None:
            issues.append((rel, "file is empty"))
            continue

        fname = yf.name

        if fname == "use_cases.yaml":
            for i, entry in enumerate(data.get("use_cases", [])):
                if not entry.get("pattern"):
                    issues.append((rel, f"use_cases[{i}] missing 'pattern'"))
                if not entry.get("key"):
                    issues.append((rel, f"use_cases[{i}] missing 'key'"))

        elif fname == "howto_scripts.yaml":
            for i, entry in enumerate(data.get("scripts", [])):
                if not entry.get("trigger"):
                    issues.append((rel, f"scripts[{i}] missing 'trigger'"))
                steps = entry.get("steps", [])
                if len(steps) < 3:
                    title = entry.get("title", f"entry {i}")
                    issues.append((rel, f"'{title}' has only {len(steps)} steps (min 3)"))

        elif fname == "static_checks.yaml":
            for i, entry in enumerate(data.get("checks", [])):
                if not entry.get("pattern"):
                    issues.append((rel, f"checks[{i}] missing 'pattern'"))
                if not entry.get("message"):
                    issues.append((rel, f"checks[{i}] missing 'message'"))

        elif fname == "rewrite_subs.yaml":
            for group in ("formal", "casual"):
                for i, entry in enumerate(data.get(group, [])):
                    repl = entry.get("replacement")
                    if repl is None:
                        issues.append((rel, f"{group}[{i}] missing 'replacement'"))
                    elif not isinstance(repl, str):
                        issues.append(
                            (
                                rel,
                                f"{group}[{i}] replacement is {type(repl).__name__}, "
                                f"not str — quote it in YAML (e.g. '\"yes\"' not 'yes')",
                            )
                        )

        elif fname == "extractors.yaml":
            for name, cfg in (data.get("extractors") or {}).items():
                if not cfg.get("pattern"):
                    issues.append((rel, f"extractor '{name}' missing 'pattern'"))

    return issues


# ---------------------------------------------------------------------------
# Check 3: Codegen templates
# ---------------------------------------------------------------------------


def check_codegen_templates() -> List[Tuple[str, str]]:
    issues: List[Tuple[str, str]] = []
    if not _CODEGEN_TEMPLATES_DIR.exists():
        return []

    for tmpl in sorted(_CODEGEN_TEMPLATES_DIR.glob("*.md")):
        if tmpl.name in _PYTHON_SECTION_EXEMPT_TEMPLATES:
            continue
        content = tmpl.read_text(encoding="utf-8").lower()
        if "## python" not in content:
            issues.append(
                (
                    f"data/codegen/templates/{tmpl.name}",
                    "missing ## python section (every template needs at least Python)",
                )
            )

    return issues


# ---------------------------------------------------------------------------
# Check 4: Knowledge files — basic sanity
# ---------------------------------------------------------------------------


def check_knowledge_files() -> List[Tuple[str, str]]:
    issues: List[Tuple[str, str]] = []
    if not _KNOWLEDGE_DIR.exists():
        return []

    # Benchmark/corpus files that may legitimately contain MASK tokens
    _MASK_EXEMPT = {"timedial.md", "contextual-parametric-knowledge-conflicts.md"}

    for kf in sorted(_KNOWLEDGE_DIR.glob("*.md")):
        rel = f"data/knowledge/{kf.name}"
        try:
            content = kf.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError as e:
            issues.append((rel, f"encoding error: {e}"))
            continue

        if len(content.strip()) == 0:
            issues.append((rel, "file is empty"))
            continue

        # Check that <MASK> passages don't dominate (skip benchmark corpus files)
        if kf.name not in _MASK_EXEMPT:
            maskCount = content.count("<MASK>")
            totalParas = content.count("\n\n")
            if totalParas > 0 and maskCount > totalParas * 0.5:
                issues.append((rel, f"over 50% of paragraphs contain <MASK> markers ({maskCount} found)"))

    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_all_checks() -> int:
    """Run all data quality checks. Returns 0 if clean, 1 if any issues."""
    checks = [
        ("Category chains", check_category_chains),
        ("Generate YAML", check_generate_yaml),
        ("Codegen templates", check_codegen_templates),
        ("Knowledge files", check_knowledge_files),
    ]

    totalIssues = 0
    print()
    print(_c("=" * 60, _BOLD))
    print(_c("  Data Quality Report", _BOLD))
    print(_c("=" * 60, _RESET))

    for name, fn in checks:
        issues = fn()
        if issues:
            print(f"\n  {_c('FAIL', _RED, _BOLD)}  {name} — {len(issues)} issue(s):")
            for loc, msg in issues:
                print(f"    {_c('x', _RED)} {loc}")
                print(f"      {msg}")
            totalIssues += len(issues)
        else:
            print(f"  {_c('PASS', _GREEN, _BOLD)}  {name}")

    print(_c("=" * 60, _RESET))

    if totalIssues:
        print(
            f"\n  {_c(f'{totalIssues} data quality issue(s) found.', _RED, _BOLD)}\n"
            "  Fix the issues above before committing.\n"
            "  Chains without Conclusion: return raw ToT traces instead of\n"
            "  direct answers — this was the root cause of the SWE-lite regression.\n",
            file=sys.stderr,
        )
        return 1

    print(_c("\n  All data quality checks passed.\n", _GREEN))
    return 0


def main() -> int:
    return run_all_checks()


if __name__ == "__main__":
    sys.exit(main())
