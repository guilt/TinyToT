"""
tinytot.generate — Use-case handlers for the 80-90% of GenAI workloads.

All content (patterns, word lists, templates, substitutions) lives in
data/generate/*.yaml and data/generate/creative/*.yaml — this module is
pure dispatch logic that loads and applies that data.

Covered use cases (keys):
  rewrite_code  idiomatic/Pythonic code rewrite
  rewrite       text register shift (formal, casual, concise, …)
  extract       structured entity extraction (emails, URLs, dates, …)
  table         markdown comparison tables and pros/cons scaffolds
  brainstorm    numbered idea lists
  debug_inline  static analysis of pasted code
  howto         step-by-step procedural guides
  uncertainty   honest calibrated non-answer for unknowable futures
  multidoc      compare two stated positions / documents
  creative      haiku, poems, story continuations, dialogues
"""

from __future__ import annotations

import ast
import re
import textwrap
from functools import lru_cache
from typing import Optional

__all__ = [
    "detectUseCase",
    "handleUseCase",
]

from tinytot.content import DATA_DIR as _TINYTOT_DATA_DIR

_DATA_DIR = _TINYTOT_DATA_DIR / "generate"

# ---------------------------------------------------------------------------
# Data loaders — one lru_cache per file, cleared on demand
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _loadUseCases() -> list[tuple[re.Pattern[str], str]]:
    """Load use-case detection patterns from use_cases.yaml."""
    import yaml

    path = _DATA_DIR / "use_cases.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    result = []
    for entry in data.get("use_cases", []):
        flags = re.IGNORECASE
        if "DOTALL" in entry.get("flags", ""):
            flags |= re.DOTALL
        pat = re.compile(entry["pattern"], flags)
        result.append((pat, entry["key"]))
    return result


@lru_cache(maxsize=1)
def _loadRewriteSubs() -> dict[str, list[tuple[re.Pattern[str], str]]]:
    """Load formality/casual substitution tables from rewrite_subs.yaml."""
    import yaml

    path = _DATA_DIR / "rewrite_subs.yaml"
    if not path.exists():
        return {"formal": [], "casual": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    result: dict[str, list[tuple[re.Pattern[str], str]]] = {}
    for group in ("formal", "casual"):
        result[group] = [
            (re.compile(entry["pattern"], re.IGNORECASE), str(entry["replacement"])) for entry in data.get(group, [])
        ]
    return result


@lru_cache(maxsize=1)
def _loadExtractors() -> tuple[dict[str, re.Pattern[str]], dict[str, str]]:
    """Load entity extractors and synonym map from extractors.yaml."""
    import yaml

    path = _DATA_DIR / "extractors.yaml"
    if not path.exists():
        return {}, {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    patterns: dict[str, re.Pattern[str]] = {}
    synonyms: dict[str, str] = {}
    for key, cfg in data.get("extractors", {}).items():
        patterns[key] = re.compile(cfg["pattern"], re.IGNORECASE)
        for alias in cfg.get("synonyms", []):
            synonyms[alias] = key
    return patterns, synonyms


@lru_cache(maxsize=1)
def _loadStaticChecks() -> list[tuple[re.Pattern[str], str]]:
    """Load static code analysis checks from static_checks.yaml."""
    import yaml

    path = _DATA_DIR / "static_checks.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [
        (re.compile(entry["pattern"], re.IGNORECASE | re.DOTALL), entry["message"]) for entry in data.get("checks", [])
    ]


@lru_cache(maxsize=1)
def _loadPythonicSubs() -> list[tuple[re.Pattern[str], str, str]]:
    """Load Pythonic rewrite substitutions from pythonic_subs.yaml."""
    import yaml

    path = _DATA_DIR / "pythonic_subs.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    result = []
    for entry in data.get("substitutions", []):
        flags = re.MULTILINE if "MULTILINE" in entry.get("flags", "") else 0
        result.append(
            (
                re.compile(entry["pattern"], flags),
                entry["replacement"],
                entry.get("description", ""),
            )
        )
    return result


@lru_cache(maxsize=1)
def _loadHowToScripts() -> list[tuple[re.Pattern[str], str, list[str]]]:
    """Load how-to step scripts from howto_scripts.yaml."""
    import yaml

    path = _DATA_DIR / "howto_scripts.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [
        (
            re.compile(entry["trigger"], re.IGNORECASE),
            entry.get("title", ""),
            entry.get("steps", []),
        )
        for entry in data.get("scripts", [])
    ]


@lru_cache(maxsize=1)
def _loadUncertaintyTopics() -> list[str]:
    """Load unknowable topic keywords from uncertainty.yaml."""
    import yaml

    path = _DATA_DIR / "uncertainty.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [t.lower() for t in data.get("topics", [])]


@lru_cache(maxsize=1)
def _loadContradictionPairs() -> list[tuple[str, str]]:
    """Load polarity opposition pairs from contradiction_pairs.yaml."""
    import yaml

    path = _DATA_DIR / "contradiction_pairs.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [(str(p[0]), str(p[1])) for p in data.get("pairs", [])]


@lru_cache(maxsize=1)
def _loadHaikuTopics() -> dict[str, tuple[str, str, str]]:
    """Load haiku word-banks from creative/haiku_topics.yaml."""
    import yaml

    path = _DATA_DIR / "creative" / "haiku_topics.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    result: dict[str, tuple[str, str, str]] = {}
    for key, cfg in data.get("topics", {}).items():
        triple = (cfg["line1"], cfg["line2"], cfg["line3"])
        result[key] = triple
        for alias in cfg.get("aliases", []):
            result[alias] = triple
    return result


@lru_cache(maxsize=1)
def _loadStoryTemplates() -> list[tuple[str, str]]:
    """Load story continuation templates from creative/story_templates.yaml."""
    import yaml

    path = _DATA_DIR / "creative" / "story_templates.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [(entry["trigger"], entry["text"]) for entry in data.get("templates", [])]


# ---------------------------------------------------------------------------
# Use-case detection (data-driven)
# ---------------------------------------------------------------------------


def detectUseCase(prompt: str) -> Optional[str]:
    """Return the use-case key if the prompt matches any pattern, else None.

    Checks use_cases.yaml patterns first, then falls back to checking
    howto_scripts.yaml triggers directly — so any how-to guide can be
    triggered without needing a matching use_case pattern.
    """
    for pat, key in _loadUseCases():
        if pat.search(prompt):
            return key
    # Fallback: if any howto_script trigger matches, route to howto
    for script_re, _, _ in _loadHowToScripts():
        if script_re.search(prompt):
            return "howto"
    return None


# ---------------------------------------------------------------------------
# Helper: extract inline code from prompt body
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```[\w]*\n?(.*?)```", re.DOTALL)
_INDENT_CODE_RE = re.compile(r"(?:(?:^|\n)    .+)+", re.MULTILINE)


def _extract_inline_code(prompt: str) -> Optional[str]:
    m = _FENCE_RE.search(prompt)
    if m:
        return m.group(1).strip()
    m = _INDENT_CODE_RE.search(prompt)
    if m:
        return textwrap.dedent(m.group(0)).strip()
    if re.search(r"\bdef\s+\w+\s*\(|\bfor\s+\w+\s+in\s+|=\s*\[|import\s+\w+", prompt):
        for prefix_re in [
            re.compile(r"^.*?(?:fix|rewrite|debug|here is|following).*?:\s*", re.I | re.DOTALL),
            re.compile(r"^.*?:\s*", re.DOTALL),
        ]:
            stripped = prefix_re.sub("", prompt, count=1).strip()
            if stripped and re.search(r"\bdef\s+|\bfor\s+|\bimport\s+", stripped):
                return stripped
    return None


# ---------------------------------------------------------------------------
# Handler 1: Text rewrite / register shift
# ---------------------------------------------------------------------------

_REGISTER_RE = re.compile(
    r"\b(formal|professional|informal|casual|concise|shorter|simpler|cleaner|"
    r"elaborate|detailed|longer|polite|friendly|academic|technical|plain)\b",
    re.I,
)


def _extract_subject_text(prompt: str) -> str:
    for sep in (":\n", ": ", "—", "–", " - ", "\n"):
        if sep in prompt:
            parts = prompt.split(sep, 1)
            candidate = parts[-1].strip()
            if len(candidate) > 5:
                return candidate
    return (
        re.sub(
            r"^.*?(?:rewrite|paraphrase|make|improve|fix)\s+(?:this|it|the\s+following)\s*[:\-]?\s*",
            "",
            prompt,
            flags=re.I,
        ).strip()
        or prompt
    )


def _handle_rewrite(prompt: str) -> str:
    registerM = _REGISTER_RE.search(prompt)
    register = registerM.group(1).lower() if registerM else "formal"
    text = _extract_subject_text(prompt)

    if not text or text == prompt:
        return (
            "To rewrite text, provide the content after a colon. For example:\n"
            '  "Make this more formal: hey wanna grab lunch tomorrow?"\n\n'
            "Supported registers: formal, casual, concise, elaborate, polite, technical, academic."
        )

    subs = _loadRewriteSubs()
    if register in ("formal", "professional", "academic", "polite"):
        result = text
        for pat, sub in subs.get("formal", []):
            result = pat.sub(sub, result)
        result = result.strip()
        if result and result[0].islower():
            result = result[0].upper() + result[1:]
        if result and result[-1] not in ".!?":
            result += "."
        label = "Formal"
    elif register in ("casual", "informal", "friendly"):
        result = text
        for pat, sub in subs.get("casual", []):
            result = pat.sub(sub, result)
        label = "Casual"
    elif register in ("concise", "shorter", "brief"):
        result = re.sub(r"\b(?:basically|essentially|in\s+order\s+to|the\s+fact\s+that)\b", "", text, flags=re.I)
        result = re.sub(r"\s{2,}", " ", result).strip()
        label = "Concise"
    elif register in ("simpler", "plain", "simple"):
        result = text
        for pat, sub in subs.get("casual", []):
            result = pat.sub(sub, result)
        label = "Simplified"
    else:
        result = text
        label = register.capitalize()

    return f"**{label} version:**\n\n{result}\n\n*Register applied: {register}*"


# ---------------------------------------------------------------------------
# Handler 2: Structured extraction
# ---------------------------------------------------------------------------

_TARGET_RE = re.compile(
    r"\b(email|url|link|date|phone|number|hashtag|mention|ip|name|entity|keyword)\b",
    re.I,
)


def _handle_extract(prompt: str) -> str:
    targetM = _TARGET_RE.search(prompt)
    target = targetM.group(1).lower() if targetM else "email"

    patterns, synonyms = _loadExtractors()
    canonical = synonyms.get(target, target)

    body = re.sub(
        r"^.*?(?:extract|find|pull\s+out|list)\s+(?:all\s+)?[^:]+:\s*",
        "",
        prompt,
        flags=re.I,
    ).strip()
    if not body or body == prompt:
        m = re.split(r"\b(?:from|in)\s+(?:this\s+)?(?:text|paragraph|email|message)\s*:?\s*", prompt, flags=re.I)
        body = m[-1].strip() if len(m) > 1 else prompt

    extractor = patterns.get(canonical)
    if extractor:
        matches = extractor.findall(body)
    else:
        matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", body)

    if not matches:
        return f"No {target}s found in the provided text."

    lines = [f"**Extracted {target}s ({len(matches)} found):**", ""]
    for m in matches:
        lines.append(f"- `{m}`")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Handler 3: Table / comparison / pros-cons
# ---------------------------------------------------------------------------

_SUBJECTS_RE = re.compile(
    r"\bcompare\b\s+([\w\s,/+]+?)\s+(?:and|vs|versus|or)\s+([\w\s/+]+?)(?:\s+(?:table|side|pros|benefits|tradeoff)|\b|$)",
    re.I,
)
_PROS_CONS_RE = re.compile(
    r"\bpros\s+and\s+cons\b|\badvantages\s+and\s+disadvantages\b|\bbenefits?\s+and\s+drawbacks?\b",
    re.I,
)
_SUBJECT_OF_RE = re.compile(
    r"(?:pros\s+and\s+cons|advantages\s+and\s+disadvantages|tradeoffs?)\s+of\s+([\w\s,/+\-]+?)(?:\s*$|\s*[\?\.\!])",
    re.I,
)


def _handle_table(prompt: str) -> str:
    if _PROS_CONS_RE.search(prompt):
        subj_m = _SUBJECT_OF_RE.search(prompt)
        subject = subj_m.group(1).strip() if subj_m else "this approach"
        return (
            f"**Pros and Cons: {subject.title()}**\n\n"
            f"| Pros | Cons |\n"
            f"|------|------|\n"
            f"| Clear and focused | Can be too narrow |\n"
            f"| Well-established patterns | Requires upfront investment |\n"
            f"| Widely understood | May not fit all contexts |\n"
            f"| Testable and verifiable | Adds complexity at scale |\n\n"
            f"*To get specific pros/cons, describe your use case after the colon.*"
        )

    m = _SUBJECTS_RE.search(prompt)
    if m:
        a, b = m.group(1).strip(), m.group(2).strip()
    else:
        parts = re.split(
            r"\s+(?:and|vs\.?|versus|or)\s+", re.sub(r"^.*?compare\s+", "", prompt, flags=re.I), maxsplit=1
        )
        if len(parts) == 2:
            a, b = parts[0].strip(), parts[1].strip().rstrip("?.!")
        else:
            return (
                "**Comparison Table**\n\n"
                "| Feature | Option A | Option B |\n"
                "|---------|----------|----------|\n"
                "| Performance | — | — |\n"
                "| Ease of use | — | — |\n"
                "| Scalability | — | — |\n"
                "| Community | — | — |\n\n"
                "*Specify what to compare: e.g. 'Compare Python and JavaScript'*"
            )

    return (
        f"**Comparison: {a.title()} vs {b.title()}**\n\n"
        f"| Feature | {a.title()} | {b.title()} |\n"
        f"|---------|{'—' * (len(a) + 2)}|{'—' * (len(b) + 2)}|\n"
        f"| Primary use | — | — |\n"
        f"| Learning curve | — | — |\n"
        f"| Performance | — | — |\n"
        f"| Ecosystem | — | — |\n"
        f"| Best for | — | — |\n\n"
        f"*Scaffold — fill in the cells or ask about a specific aspect: "
        f"'Compare {a} and {b} for data science'.*"
    )


# ---------------------------------------------------------------------------
# Handler 4: Brainstorm / idea list
# ---------------------------------------------------------------------------

_COUNT_RE = re.compile(r"\b(\d+)\s+(?:ideas?|suggestions?|examples?|options?|ways?|reasons?|tips?)\b", re.I)
_TOPIC_FROM_BRAINSTORM_RE = re.compile(
    r"(?:ideas?\s+for|suggestions?\s+for|ways?\s+to|examples?\s+of|options?\s+for)\s+([\w\s,/\-]+?)(?:\s*$|\s*[\?\.\!])",
    re.I,
)


def _handle_brainstorm(prompt: str) -> str:
    count_m = _COUNT_RE.search(prompt)
    n = min(int(count_m.group(1)) if count_m else 5, 10)
    topicM = _TOPIC_FROM_BRAINSTORM_RE.search(prompt)
    topic = topicM.group(1).strip() if topicM else "this topic"
    lines = [f"**{n} ideas for {topic}:**", ""]
    for i in range(1, n + 1):
        lines.append(f"{i}. *(idea {i} — describe your constraints and I can generate more specific suggestions)*")
    lines += [
        "",
        "*To get concrete ideas, describe: your target audience, constraints, and goals.*",
        "*Example: 'Give me 5 ideas for a mobile app for elderly users with limited tech skills'*",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Handler 5: Inline code debug (static analysis via ast + data/generate/static_checks.yaml)
# ---------------------------------------------------------------------------


def _handle_debug_inline(prompt: str) -> str:
    code = _extract_inline_code(prompt)
    if not code:
        return (
            "I can debug code you paste directly.\n\n"
            "Paste your code in a fenced block:\n"
            "```python\n# your code here\n```\n"
            "or describe the error you're seeing."
        )

    issues: list[str] = []

    try:
        tree = ast.parse(code)
        syntax_ok = True
    except SyntaxError as e:
        syntax_ok = False
        issues.append(f"**Syntax error** on line {e.lineno}: `{e.msg}`")
        if e.text:
            issues.append(f"  Near: `{e.text.strip()}`")
        issues.append("  Fix: check for missing colons, unmatched brackets, or incorrect indentation.")

    if syntax_ok:
        for check_re, message in _loadStaticChecks():
            if check_re.search(code):
                issues.append(f"⚠ {message}")

        try:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found_return = False
                    for child in ast.iter_child_nodes(node):
                        if found_return and not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            issues.append(f"⚠ Unreachable code after `return` in `{node.name}()`")
                            break
                        if isinstance(child, ast.Return):
                            found_return = True
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.FloorDiv):
                    issues.append("⚠ Integer floor division `//` — verify this is intentional (not a missing `/`)")
        except Exception:
            pass

    if not issues:
        return (
            "No obvious static issues found.\n\n"
            "```python\n" + code + "\n```\n\n"
            "The code parses cleanly. Describe the unexpected behaviour to get targeted advice."
        )

    result = (
        ["**Static analysis results:**", ""]
        + issues
        + [
            "",
            "**Your code:**",
            "```python",
            code,
            "```",
        ]
    )
    return "\n".join(result)


# ---------------------------------------------------------------------------
# Handler 6: Inline code rewrite (Pythonic — data/generate/pythonic_subs.yaml)
# ---------------------------------------------------------------------------


def _handle_rewrite_code(prompt: str) -> str:
    code = _extract_inline_code(prompt)
    if not code:
        return "Paste the code you want rewritten in a fenced block:\n```python\n# your code here\n```"

    result = code
    applied: list[str] = []
    for pat, repl, desc in _loadPythonicSubs():
        new = pat.sub(repl, result)
        if new != result:
            applied.append(desc)
            result = new

    if not applied:
        return (
            "The code already looks fairly idiomatic. Here it is with minor style notes:\n\n"
            "```python\n" + code + "\n```\n\n"
            "Consider: type hints, docstrings, and `pathlib.Path` instead of `os.path`."
        )

    return (
        f"**Pythonic rewrite** (applied: {', '.join(applied)}):\n\n"
        f"```python\n{result}\n```\n\n"
        f"**Original:**\n```python\n{code}\n```"
    )


# ---------------------------------------------------------------------------
# Handler 7: Step-by-step how-to (data/generate/howto_scripts.yaml)
# ---------------------------------------------------------------------------


def _handle_howto(prompt: str) -> str:
    for script_re, title, steps in _loadHowToScripts():
        if script_re.search(prompt):
            lines = [f"**{title}:**" if title else "**Step-by-step guide:**", ""]
            for i, step in enumerate(steps, 1):
                lines.append(f"{i}. {step}")
            return "\n".join(lines)

    topicM = re.search(
        r"how\s+(?:do\s+I|to)\s+([\w\s]+?)(?:\s*$|\s*[\?\.\!])"
        r"|walk\s+me\s+through\s+([\w\s]+?)(?:\s*$|\s*[\?\.\!])"
        r"|set\s+up\s+(?:a\s+)?([\w\s]+?)(?:\s*$|\s*[\?\.\!])",
        prompt,
        re.I,
    )
    topic = next((g for g in (topicM.groups() if topicM else []) if g), "this").strip()

    return (
        f"**How to {topic} — general steps:**\n\n"
        "1. Understand the prerequisites and install required tools\n"
        "2. Create the necessary project structure\n"
        "3. Configure your environment and dependencies\n"
        "4. Write the core logic following best practices\n"
        "5. Test your implementation\n"
        "6. Document and version control your work\n\n"
        f"*For step-by-step instructions on a specific workflow, describe the exact tool "
        f"or language. Built-in guides cover: Python venv, Docker, Git, pytest, "
        f"cloud deployment, React, databases, and CSV processing.*"
    )


# ---------------------------------------------------------------------------
# Handler 8: Calibrated uncertainty (data/generate/uncertainty.yaml)
# ---------------------------------------------------------------------------


def _handle_uncertainty(prompt: str) -> str:
    p = prompt.lower()
    topic = next((t for t in _loadUncertaintyTopics() if t in p), "this")
    return (
        f"I genuinely don't know — and neither does anyone else with certainty. "
        f"Predicting {topic} outcomes involves inherent uncertainty that no model can resolve.\n\n"
        f"**What I can tell you:**\n"
        f"- I don't have access to real-time data.\n"
        f"- Historical patterns exist but past performance doesn't guarantee future results.\n"
        f"- For actionable forecasts, consult domain-specific sources: weather services, "
        f"financial analysts, or current news.\n\n"
        f"*A model that confidently predicts {topic} outcomes is overconfident or pattern-matching "
        f"on training data, not reasoning.*"
    )


# ---------------------------------------------------------------------------
# Handler 9: Multi-document synthesis (data/generate/contradiction_pairs.yaml)
# ---------------------------------------------------------------------------

_DOC_MARKER_RE = re.compile(
    r"(?:doc(?:ument)?|source|paper|article|text|passage)\s*[12]\s*(?:says?|states?|argues?|claims?|asserts?)?\s*[:\-]?\s*(.+?)(?=\n|doc(?:ument)?|source|paper|article|text|passage\s*[12]|$)",
    re.I | re.DOTALL,
)
_SAYS_RE = re.compile(
    r"(?:one\s+(?:says?|argues?|claims?|states?)|first\s+(?:says?|claims?)|doc\s*1\s*(?:says?|:))\s*[:\"]?\s*(.+?)\s*(?:[.!]|$).{0,10}?"
    r"(?:other\s+(?:says?|argues?|claims?|states?)|second\s+(?:says?|claims?)|doc\s*2\s*(?:says?|:))\s*[:\"]?\s*(.+?)(?:[.!?]|$)",
    re.I | re.DOTALL,
)


def _handle_multidoc(prompt: str) -> str:
    docs = _DOC_MARKER_RE.findall(prompt)
    if len(docs) < 2:
        m = _SAYS_RE.search(prompt)
        if m:
            docs = [m.group(1).strip(), m.group(2).strip()]
    if len(docs) < 2:
        docs = re.findall(r"['\"]([^'\"]{10,})['\"]", prompt)

    if len(docs) < 2:
        return (
            "To compare documents or sources, provide both positions clearly:\n"
            "  *Doc1: [first position]. Doc2: [second position]. What do they agree on?*"
        )

    s1, s2 = docs[0].strip().rstrip("."), docs[1].strip().rstrip(".")
    t1 = set(re.findall(r"\b\w{4,}\b", s1.lower()))
    t2 = set(re.findall(r"\b\w{4,}\b", s2.lower()))
    stop = {
        "that",
        "this",
        "with",
        "from",
        "they",
        "their",
        "have",
        "been",
        "more",
        "also",
        "than",
        "into",
        "some",
        "most",
        "which",
    }
    shared = (t1 & t2) - stop

    contradictions = []
    for pos, neg in _loadContradictionPairs():
        if pos in s1.lower() and neg in s2.lower():
            contradictions.append(f"'{pos}' vs '{neg}'")
        if neg in s1.lower() and pos in s2.lower():
            contradictions.append(f"'{neg}' vs '{pos}'")

    lines = ["**Document synthesis:**", "", f"**Position 1:** {s1}.", f"**Position 2:** {s2}.", ""]
    if shared:
        lines.append(f"**Common ground:** Both mention — {', '.join(sorted(shared)[:6])}.")
    else:
        lines.append("**Common ground:** No obvious shared vocabulary detected.")

    if contradictions:
        lines.append(f"**Disagreement:** Opposing claims — {'; '.join(contradictions)}.")
        lines.append("")
        lines.append(
            "*These positions directly conflict. Look for: different scopes, different "
            "evidence bases, or different definitions of key terms.*"
        )
    else:
        lines.append("**Relationship:** No direct contradiction detected — positions may be complementary.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Handler 10: Creative writing (data/generate/creative/*.yaml)
# ---------------------------------------------------------------------------


def _extract_creative_topic(prompt: str) -> str:
    for pat in [
        re.compile(r"(?:about|on|of|for)\s+(?:the\s+)?(\w+)", re.I),
        re.compile(r"(?:haiku|poem|story)\s+(?:about\s+)?(\w+)", re.I),
    ]:
        m = pat.search(prompt)
        if m:
            return m.group(1).lower()
    return "default"


def _handle_creative(prompt: str) -> str:
    p = prompt.lower()
    topic = _extract_creative_topic(prompt)
    haiku_topics = _loadHaikuTopics()
    story_templates = _loadStoryTemplates()

    # --- Haiku ---
    if re.search(r"\bhaiku\b", p):
        lines = haiku_topics.get(topic, haiku_topics.get("default", ("...", "...", "...")))
        return f"**Haiku ({topic}):**\n\n{lines[0]}\n{lines[1]}\n{lines[2]}"

    # --- Poem ---
    if re.search(r"\bpoem\b|\bverse\b|\bsonnet\b|\bode\b", p):
        lines = haiku_topics.get(topic, haiku_topics.get("default", ("...", "...", "...")))
        return (
            f"**Poem — {topic.capitalize()}:**\n\n"
            f"{lines[0]}.\n"
            f"And still — {lines[1].lower()}.\n\n"
            f"We look for meaning in the shape of things,\n"
            f"In {topic}, in silence, in the space between.\n\n"
            f"{lines[2]}.\n\n"
            f"*Template poem — for fully original verse a generative model is needed.*"
        )

    # --- Story continuation ---
    if re.search(r"\bcontinue\b|\bstory\b|\btale\b", p):
        for trigger, template in story_templates:
            if trigger in p:
                pronoun = "She" if re.search(r"\bshe\b", p) else "He"
                return (
                    "**Story continuation:**\n\n"
                    + template.format(pronoun=pronoun)
                    + "\n\n*Continuation from structural template.*"
                )
        seed_m = re.search(r"(?:story:|passage:|tale:)\s*(.+)", prompt, re.I | re.DOTALL)
        seed = seed_m.group(1).strip() if seed_m else prompt
        return (
            "**Story continuation:**\n\n"
            f"{seed.rstrip('.')} — but nothing was as it seemed. "
            "What followed would change everything.\n\n"
            "*Structural stub — genuine generation requires a language model.*"
        )

    # --- Dialogue ---
    if re.search(r"\bdialogue\b|\bconversation\b", p):
        speakers = re.findall(r"\ba\s+(\w+)\s+and\s+a\s+(\w+)\b|\bbetween\s+a\s+(\w+)\s+and\s+a\s+(\w+)\b", p)
        if speakers:
            flat = [s for s in speakers[0] if s]
            a, b = (flat + ["Person A", "Person B"])[:2]
        else:
            a, b = "Person A", "Person B"
        subject_m = re.search(r"\babout\s+(\w[\w\s]+?)(?:\s*$|\?|\.)", p)
        subject = subject_m.group(1).strip() if subject_m else topic
        return (
            f"**Dialogue — {a.capitalize()} and {b.capitalize()} discuss {subject}:**\n\n"
            f"**{a.capitalize()}:** Can you explain {subject} simply?\n\n"
            f"**{b.capitalize()}:** At its core, {subject} is about how things interact when the rules change.\n\n"
            f"**{a.capitalize()}:** But why does that matter?\n\n"
            f"**{b.capitalize()}:** Because once you understand {subject}, you see it everywhere.\n\n"
            f"**{a.capitalize()}:** I need an example.\n\n"
            f"**{b.capitalize()}:** *(smiles)* Don't we all.\n\n"
            "*Structural dialogue scaffold — generative dialogue requires a language model.*"
        )

    # Generic fallback
    return (
        f"**Creative writing — {topic}:**\n\n"
        f"The thing about {topic} is that it always arrives differently than you expect.\n\n"
        "*For original creative content I need a specific form — haiku, poem, story, or dialogue — "
        "plus context (characters, setting, tone). I can generate structural templates for all of these. "
        "Fully original prose requires an LLM.*"
    )


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

_HANDLERS = {
    "rewrite": _handle_rewrite,
    "extract": _handle_extract,
    "table": _handle_table,
    "brainstorm": _handle_brainstorm,
    "debug_inline": _handle_debug_inline,
    "rewrite_code": _handle_rewrite_code,
    "howto": _handle_howto,
    "uncertainty": _handle_uncertainty,
    "multidoc": _handle_multidoc,
    "creative": _handle_creative,
}


def handleUseCase(use_case: str, prompt: str) -> Optional[str]:
    """Dispatch to the handler for the detected use case."""
    fn = _HANDLERS.get(use_case)
    return fn(prompt) if fn else None
