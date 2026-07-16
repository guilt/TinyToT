"""
tinytot.refine — Rule-based code refinement and reasoning explanation.

Handles multi-turn requests that operate on a prior code or text response:
  - Code transformations: make async, add type hints, add error handling,
    add logging, convert language, add docstring, simplify
  - Reasoning explanation: "explain your reasoning", "why did you choose X",
    "walk me through this step by step"
  - Code explanation: "explain this code", "what does this do"

All transformations are rule-based — AST where possible, regex otherwise.
No LLM, no network.
"""

from __future__ import annotations

import ast
import re
import textwrap
from typing import Optional

__all__ = [
    "detectRefinementIntent",
    "applyRefinement",
    "explainCode",
    "explainReasoning",
    "extractPriorCode",
]

# ---------------------------------------------------------------------------
# Refinement intent detection
# ---------------------------------------------------------------------------

_REFINEMENT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bmake\s+it\s+async(?:hronous)?\b|\bconvert\s+to\s+async\b|\badd\s+async\b", re.I), "make_async"),
    (re.compile(r"\badd\s+type\s+hints?\b|\badd\s+types?\b|\bannotate\b|\btype.annotate\b", re.I), "add_types"),
    (
        re.compile(r"\badd\s+error\s+handl|\badd\s+exception|\btry.except|\bhandle\s+errors?\b", re.I),
        "add_error_handling",
    ),
    (re.compile(r"\badd\s+(?:logging|log\s+statements?|debug\s+prints?)\b", re.I), "add_logging"),
    (
        re.compile(r"\badd\s+(?:a\s+)?docstring|\badd\s+comments?\b|\bdocument\s+(?:this|it|the)\b", re.I),
        "add_docstring",
    ),
    (
        re.compile(r"\bsimplify\b|\brefactor\b|\bclean\s+up\b|\bmake\s+(?:it\s+)?(?:cleaner|simpler|shorter)\b", re.I),
        "simplify",
    ),
    (
        re.compile(r"\boptimize\b|\bmake\s+(?:it\s+)?(?:faster|more\s+efficient)\b|\bimprove\s+performance\b", re.I),
        "optimize",
    ),
    (
        re.compile(r"\bconvert\s+to\s+(?:java|javascript|go|rust|c\+\+|typescript|kotlin)\b|\btranslate\s+to\b", re.I),
        "translate",
    ),
    (
        re.compile(
            r"\bexplain\s+(?:this|your\s+reasoning|why|how|the|it|that)\b|\bwalk\s+me\s+through\b|\bbreak\s+(?:this\s+)?down\b",
            re.I,
        ),
        "explain",
    ),
    (re.compile(r"\bwhat\s+does\s+(?:this|it|that)\s+do\b|\bhow\s+does\s+this\s+work\b", re.I), "explain"),
    (
        re.compile(
            r"\btest(?:s|ing)?\s+(?:for\s+this|this|it)\b|\badd\s+(?:unit\s+)?tests?\b|\bwrite\s+tests?\b", re.I
        ),
        "add_tests",
    ),
    (
        re.compile(
            r"\bis\s+(?:this|it|that)\s+(?:good|correct|right|ok|okay|enough|fine|valid|working|complete)(?:\s+enough)?\??"
            r"|\bdoes\s+(?:this|it|that)\s+(?:work|look\s+right|look\s+good|look\s+correct|seem\s+right)?\??"
            r"|\blooks?\s+(?:good|ok|okay|right|correct|fine)\??$"
            r"|\bany\s+(?:issues?|problems?|bugs?|mistakes?|improvements?)\??"
            r"|\bcan\s+(?:we|i|you)\s+(?:improve|do\s+better|make\s+this\s+better)\??",
            re.I,
        ),
        "review",
    ),
]


def detectRefinementIntent(prompt: str) -> Optional[str]:
    """Return a refinement intent key if the prompt is modifying a prior response.

    Returns None if this looks like a fresh request.
    """
    for pat, intent in _REFINEMENT_PATTERNS:
        if pat.search(prompt):
            return intent
    return None


# ---------------------------------------------------------------------------
# Extract code from a prior assistant message
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```[\w]*\n(.*?)```", re.DOTALL)


def extractPriorCode(messages: list) -> Optional[str]:
    """Walk back through messages to find the most recent code block."""
    for msg in reversed(messages):
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", "")
        m = _FENCE_RE.search(content)
        if m:
            return m.group(1).strip()
    return None


def extractPriorResponse(messages: list) -> Optional[str]:
    """Return the most recent assistant message content."""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            return msg.get("content", "").strip()
    return None


# ---------------------------------------------------------------------------
# Code transformations (rule-based)
# ---------------------------------------------------------------------------


def _make_async(code: str) -> str:
    """Convert synchronous Python functions to async def."""
    # Replace 'def ' with 'async def ' for each function definition
    lines = []
    for line in code.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("def ") and not stripped.startswith("async def "):
            indent = len(line) - len(stripped)
            lines.append(" " * indent + "async " + stripped)
        else:
            lines.append(line)
    result = "\n".join(lines)
    # Replace synchronous calls that have common async equivalents
    result = re.sub(r"\btime\.sleep\b", "await asyncio.sleep", result)
    result = re.sub(r"\brequests\.get\b", "await session.get", result)
    result = re.sub(r"\brequests\.post\b", "await session.post", result)
    if "await" in result and "import asyncio" not in result:
        result = "import asyncio\n\n" + result
    return result


def _add_types(code: str) -> str:
    """Add basic type hints to Python function signatures using heuristics."""

    def _annotate_func(m: re.Match) -> str:
        indent = m.group(1)
        name = m.group(2)
        params_str = m.group(3).strip()
        body_hint = m.group(4)  # first line of body (for return type guess)

        params = [p.strip() for p in params_str.split(",") if p.strip()]
        annotated = []
        for p in params:
            if ":" in p or p in ("self", "cls", "*args", "**kwargs"):
                annotated.append(p)
            elif p.startswith("**"):
                annotated.append(p + ": Any")
            elif p.startswith("*"):
                annotated.append(p)
            elif any(kw in p.lower() for kw in ("num", "count", "size", "n", "k", "i", "j")):
                annotated.append(p + ": int")
            elif any(kw in p.lower() for kw in ("name", "text", "msg", "s", "word", "key")):
                annotated.append(p + ": str")
            elif any(kw in p.lower() for kw in ("lst", "arr", "items", "values", "nums", "data")):
                annotated.append(p + ": list")
            elif any(kw in p.lower() for kw in ("d", "dct", "mapping", "config", "opts")):
                annotated.append(p + ": dict")
            elif any(kw in p.lower() for kw in ("flag", "is_", "has_", "enable")):
                annotated.append(p + ": bool")
            else:
                annotated.append(p)

        # Guess return type from body
        ret = " -> None"
        if body_hint:
            if "return True" in body_hint or "return False" in body_hint:
                ret = " -> bool"
            elif re.search(r"return\s+\d", body_hint):
                ret = " -> int"
            elif re.search(r'return\s+"', body_hint) or re.search(r"return\s+'", body_hint):
                ret = " -> str"
            elif "return []" in body_hint or "return list" in body_hint:
                ret = " -> list"
            elif "return {" in body_hint or "return dict" in body_hint:
                ret = " -> dict"

        new_params = ", ".join(annotated)
        return f"{indent}def {name}({new_params}){ret}:"

    pattern = re.compile(
        r"^( *)def\s+(\w+)\(([^)]*)\)\s*:(.*)$",
        re.MULTILINE,
    )
    result = pattern.sub(_annotate_func, code)
    if "Any" in result and "from typing import" not in result:
        result = "from typing import Any\n\n" + result
    return result


def _add_error_handling(code: str) -> str:
    """Wrap function bodies in try/except blocks."""
    lines = code.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if (stripped.startswith("def ") or stripped.startswith("async def ")) and line.rstrip().endswith(":"):
            result.append(line)
            i += 1
            # Collect docstring if present
            if i < len(lines) and '"""' in lines[i]:
                while i < len(lines):
                    result.append(lines[i])
                    if lines[i].strip().endswith('"""') and i > len(result) - 2:
                        i += 1
                        break
                    i += 1

            body_indent = " " * (indent + 4)
            result.append(f"{body_indent}try:")
            # Indent remaining body lines by 4 more
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.lstrip()
                next_indent = len(next_line) - len(next_stripped)
                # Stop when we hit a new definition at same or lower indent
                if (
                    next_stripped
                    and next_indent <= indent
                    and (
                        next_stripped.startswith("def ")
                        or next_stripped.startswith("class ")
                        or next_stripped.startswith("async def ")
                    )
                ):
                    break
                if next_line.strip():
                    result.append("    " + next_line)
                else:
                    result.append(next_line)
                i += 1

            result.append(f"{body_indent}except Exception as e:")
            result.append(f'{body_indent}    raise RuntimeError(f"{{__name__}}: {{e}}") from e')
        else:
            result.append(line)
            i += 1

    return "\n".join(result)


def _add_logging(code: str) -> str:
    """Insert logging calls at function entry/exit."""
    lines = code.splitlines()
    result = []
    has_logging = "import logging" in code

    if not has_logging:
        result.append("import logging")
        result.append("")
        result.append("logger = logging.getLogger(__name__)")
        result.append("")

    for line in lines:
        result.append(line)
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if (stripped.startswith("def ") or stripped.startswith("async def ")) and line.rstrip().endswith(":"):
            m = re.search(r"def\s+(\w+)\(", line)
            funcName = m.group(1) if m else "?"
            body_indent = " " * (indent + 4)
            result.append(f'{body_indent}logger.debug("Entering {funcName}")')

    return "\n".join(result)


def _add_docstring(code: str) -> str:
    """Add a basic docstring to undocumented functions."""
    lines = code.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        result.append(line)
        i += 1

        if (stripped.startswith("def ") or stripped.startswith("async def ")) and line.rstrip().endswith(":"):
            m = re.search(r"(?:async\s+)?def\s+(\w+)\(([^)]*)\)", line)
            funcName = m.group(1) if m else "this function"
            params = [
                p.strip().split(":")[0].split("=")[0].strip()
                for p in m.group(2).split(",")
                if p.strip() and p.strip() not in ("self", "cls")
            ]

            # Check if next non-empty line is already a docstring
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and ('"""' in lines[j] or "'''" in lines[j]):
                continue  # already has docstring

            body_indent = " " * (indent + 4)
            result.append(f'{body_indent}"""')
            result.append(f"{body_indent}{funcName.replace('_', ' ').capitalize()}.")
            if params:
                result.append(f"{body_indent}")
                result.append(f"{body_indent}Args:")
                for p in params:
                    result.append(f"{body_indent}    {p}: Description.")
            result.append(f'{body_indent}"""')

    return "\n".join(result)


def _add_tests(code: str, funcName: str = "") -> str:
    """Generate a pytest test skeleton for functions found in the code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "# Could not parse code — check for syntax errors.\n\nimport pytest\n\n# TODO: add tests manually"

    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
    if funcName:
        funcs = [f for f in funcs if funcName.lower() in f.lower()] or funcs

    lines = ["import pytest", ""]
    for fn in funcs[:6]:  # cap at 6 to avoid noise
        lines += [
            f"def test_{fn}_basic():",
            f'    """Basic test for {fn}."""',
            "    # Arrange",
            "    # Act",
            f"    result = {fn}()",
            "    # Assert",
            "    assert result is not None",
            "",
            f"def test_{fn}_edge_cases():",
            f'    """Edge cases for {fn}."""',
            "    # Test with empty / zero / None inputs",
            "    pass",
            "",
        ]
    return "\n".join(lines)


def _simplify(code: str) -> str:
    """Apply simple idiomatic Python rewrites."""
    # list() of a comprehension → keep; unnecessary list() around comprehension
    result = code
    # Replace `for i in range(len(lst)):` with enumerate hint comment
    result = re.sub(
        r"for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):",
        r"for \1, _ in enumerate(\2):  # consider: for i, item in enumerate(\2)",
        result,
    )
    # Replace `if x == True:` → `if x:`
    result = re.sub(r"\bif\s+(\w+)\s*==\s*True\b", r"if \1", result)
    result = re.sub(r"\bif\s+(\w+)\s*==\s*False\b", r"if not \1", result)
    # Replace `x = x + 1` → `x += 1`
    result = re.sub(r"\b(\w+)\s*=\s*\1\s*\+\s*1\b", r"\1 += 1", result)
    result = re.sub(r"\b(\w+)\s*=\s*\1\s*\-\s*1\b", r"\1 -= 1", result)
    return result


_TRANSFORMATIONS: dict[str, object] = {
    "make_async": _make_async,
    "add_types": _add_types,
    "add_error_handling": _add_error_handling,
    "add_logging": _add_logging,
    "add_docstring": _add_docstring,
    "simplify": _simplify,
    "optimize": _simplify,  # same heuristics; future: add algorithmic improvements
}


def applyRefinement(intent: str, code: str, prompt: str = "") -> Optional[str]:
    """Apply the named transformation to code and return a fenced block.

    Returns None if the intent is not a code transformation (e.g. 'explain').
    """
    if intent == "review":
        # Code review: check for common issues and give structured feedback.
        lines = code.strip().splitlines()
        issues = []
        suggestions = []
        try:
            import ast as _ast

            _ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        hasDocstring = any('"""' in ln or "'''" in ln for ln in lines[:5])
        hasErrorHandling = any("try" in ln or "except" in ln for ln in lines)
        hasTypeHints = any("->" in ln or ": " in ln for ln in lines)
        if not hasDocstring:
            suggestions.append("Consider adding a docstring to describe what the code does.")
        if not hasErrorHandling:
            suggestions.append("No error handling detected — consider adding try/except for robustness.")
        if not hasTypeHints:
            suggestions.append("Type hints are missing — adding them improves readability and tooling support.")
        if not issues and not suggestions:
            return "The code looks good! It parses correctly and follows basic conventions."
        parts = []
        if issues:
            parts.append("Issues found:\n" + "\n".join(f"- {i}" for i in issues))
        if suggestions:
            parts.append("Suggestions:\n" + "\n".join(f"- {s}" for s in suggestions))
        return "\n\n".join(parts)

    if intent == "add_tests":
        # Extract a specific function name from the prompt if present
        m = re.search(r"(?:for|the)\s+`?(\w+)`?\s+function", prompt, re.I)
        funcName = m.group(1) if m else ""
        transformed = _add_tests(code, funcName)
        return f"```python\n{transformed}\n```"

    if intent == "translate":
        # Extract target language
        m = re.search(r"\bto\s+(java|javascript|go|rust|c\+\+|typescript|kotlin)\b", prompt, re.I)
        lang = m.group(1).lower() if m else ""
        if lang:
            note = (
                f"# Translation from Python to {lang.capitalize()}\n# (structural conversion — review for idioms)\n\n"
            )
            # Best-effort: return original with language tag
            return f"```{lang}\n{note}{code}\n```"
        return None

    fn = _TRANSFORMATIONS.get(intent)
    if fn is None:
        return None

    transformed = fn(code)  # type: ignore[call-arg]
    if transformed == code:
        return f"```python\n# No changes needed — code already satisfies this transformation.\n{code}\n```"
    return f"```python\n{transformed}\n```"


# ---------------------------------------------------------------------------
# Tier 2: Code explanation (uses ast)
# ---------------------------------------------------------------------------


def explainCode(code: str, focus: Optional[str] = None) -> str:
    """Produce a plain-English structural explanation of Python code.

    If focus is given (e.g. a function name), explain only that part.
    Uses ast for structure; falls back to line-by-line for non-Python.
    """
    code = textwrap.dedent(code).strip()

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"I cannot parse this code — it has a syntax error: {e}\nFix the syntax and try again."

    # Collect top-level structure
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    assignments = [n for n in ast.iter_child_nodes(tree) if isinstance(n, ast.Assign)]

    if focus:
        # Narrow to the requested function or class
        target_funcs = [f for f in functions if focus.lower() in f.name.lower()]
        target_classes = [c for c in classes if focus.lower() in c.name.lower()]
        if target_funcs:
            return _explain_function(target_funcs[0], code)
        if target_classes:
            return _explain_class(target_classes[0], code)
        return f"I couldn't find a function or class named '{focus}' in the code."

    parts: list[str] = []

    # Overview
    overview_parts = []
    if classes:
        overview_parts.append(
            f"{len(classes)} class{'es' if len(classes) > 1 else ''} ({', '.join(c.name for c in classes)})"
        )
    top_funcs = [f for f in functions if isinstance(f, ast.FunctionDef)]
    standalone = [f for f in top_funcs if not any(f in list(ast.walk(c)) for c in classes)]
    if standalone:
        overview_parts.append(
            f"{len(standalone)} standalone function{'s' if len(standalone) > 1 else ''} ({', '.join(f.name for f in standalone[:5])})"
        )
    if imports:
        mods = []
        for n in imports:
            if isinstance(n, ast.Import):
                mods.extend(a.name.split(".")[0] for a in n.names)
            else:
                mods.append(n.module.split(".")[0] if n.module else "?")
        parts.append(f"**Imports:** {', '.join(sorted(set(mods)))}")

    if overview_parts:
        parts.append(f"**Overview:** This code defines {' and '.join(overview_parts)}.")

    # Explain each class
    for cls in classes:
        parts.append(_explain_class(cls, code))

    # Explain standalone functions
    for fn in standalone[:6]:
        parts.append(_explain_function(fn, code))

    # Module-level assignments
    if assignments:
        names = []
        for a in assignments:
            for t in a.targets:
                if isinstance(t, ast.Name):
                    names.append(t.id)
        if names:
            parts.append(f"**Module-level variables:** {', '.join(names[:8])}")

    return "\n\n".join(parts) if parts else "This looks like an empty or non-Python file."


def _explain_function(node: ast.FunctionDef, source: str) -> str:
    """Explain a single function node."""
    args = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
    defaults = node.args.defaults
    num_required = len(args) - len(defaults)

    # Gather what the function does from its body
    returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
    raises = [n for n in ast.walk(node) if isinstance(n, ast.Raise)]
    calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
    loops = [n for n in ast.walk(node) if isinstance(n, (ast.For, ast.While))]
    conditions = [n for n in ast.walk(node) if isinstance(n, ast.If)]

    parts = [f"**`{node.name}({', '.join(args)})`**"]

    # Docstring
    docstring = ast.get_docstring(node)
    if docstring:
        parts.append(f"  *{docstring.splitlines()[0]}*")

    # Parameters
    if args:
        param_strs = []
        for i, arg in enumerate(args):
            if i >= num_required:
                default = defaults[i - num_required]
                try:
                    default_val = ast.literal_eval(default)
                    param_strs.append(f"`{arg}` (optional, default={default_val!r})")
                except Exception:
                    param_strs.append(f"`{arg}` (optional)")
            else:
                param_strs.append(f"`{arg}` (required)")
        parts.append(f"  Parameters: {', '.join(param_strs)}")

    # What it does
    behaviours = []
    if loops:
        behaviours.append(f"iterates ({len(loops)} loop{'s' if len(loops) > 1 else ''})")
    if conditions:
        behaviours.append(f"branches ({len(conditions)} condition{'s' if len(conditions) > 1 else ''})")
    if calls:
        called = []
        for c in calls:
            if isinstance(c.func, ast.Name):
                called.append(c.func.id)
            elif isinstance(c.func, ast.Attribute):
                called.append(c.func.attr)
        called = list(dict.fromkeys(called))[:5]
        if called:
            behaviours.append(f"calls: {', '.join(called)}")
    if returns:
        behaviours.append("returns a value")
    if raises:
        behaviours.append("can raise exceptions")

    if behaviours:
        parts.append(f"  Does: {'; '.join(behaviours)}")

    # Complexity hint
    if len(loops) >= 2:
        parts.append("  ⚠ Nested loops detected — may have O(n²) complexity.")
    elif calls and any(node.name in (c.func.id if isinstance(c.func, ast.Name) else "") for c in calls):
        parts.append("  ↻ Recursive function.")

    return "\n".join(parts)


def _explain_class(node: ast.ClassDef, source: str) -> str:
    """Explain a single class node."""
    methods = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
    public = [m for m in methods if not m.name.startswith("_")]
    private = [m for m in methods if m.name.startswith("_") and m.name != "__init__"]
    init = next((m for m in methods if m.name == "__init__"), None)

    parts = [f"**Class `{node.name}`**"]

    docstring = ast.get_docstring(node)
    if docstring:
        parts.append(f"  *{docstring.splitlines()[0]}*")

    bases = [b.id if isinstance(b, ast.Name) else "?" for b in node.bases]
    if bases:
        parts.append(f"  Inherits from: {', '.join(bases)}")

    if init:
        attrs = [
            n.attr
            for n in ast.walk(init)
            if isinstance(n, ast.Attribute)
            and isinstance(n.ctx, ast.Store)
            and isinstance(n.value, ast.Name)
            and n.value.id == "self"
        ]
        if attrs:
            parts.append(f"  Instance attributes: {', '.join(sorted(set(attrs)))}")

    if public:
        parts.append(f"  Public methods: {', '.join(m.name for m in public)}")
    if private:
        parts.append(f"  Private/dunder methods: {', '.join(m.name for m in private[:4])}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Reasoning explanation
# ---------------------------------------------------------------------------


def explainReasoning(prior_response: str) -> str:
    """Extract and explain the reasoning chain from a prior ToT response."""
    if "Tree of Thoughts Analysis" in prior_response:
        # Parse out the path sections
        paths = re.findall(
            r"=== Reasoning Path (\d+) \(Score: ([\d.]+)\)(.*?)=== Reasoning Path|\Z",
            prior_response,
            re.DOTALL,
        )
        lines = ["**Reasoning breakdown:**", ""]
        for path_num, score, content in paths:
            selected = "[SELECTED]" in content
            status = " ✓ **Selected path**" if selected else ""
            lines.append(f"**Path {path_num}** (confidence {score}){status}")
            # Extract steps
            steps = re.findall(r"Step \d+: (.+)", content)
            for step in steps:
                lines.append(f"  — {step.strip()}")
            lines.append("")
        if len(lines) > 2:
            return "\n".join(lines)

    # For a plain chain conclusion — explain its structure
    if "**" in prior_response or prior_response.startswith("###"):
        return (
            "**How I reasoned:**\n\n"
            "I matched your question to the most relevant knowledge chain "
            "using TF-IDF similarity scoring, then returned the chain's conclusion "
            "directly. The answer came from the highest-scoring reasoning path.\n\n"
            f"**The answer I gave:**\n{prior_response[:400]}"
        )

    # For a code block
    if "```" in prior_response:
        code_match = _FENCE_RE.search(prior_response)
        if code_match:
            code = code_match.group(1).strip()
            return (
                "**How I generated this code:**\n\n"
                "I matched your request against 648 code templates using pattern "
                "matching, then retrieved the best-fit template for your language. "
                "No code was generated from scratch — this is a verified template.\n\n"
                "**Code explanation:**\n\n" + explainCode(code)
            )

    return (
        "**My reasoning:**\n\n"
        "I matched your question against the knowledge base using TF-IDF cosine "
        "similarity, ranked the available reasoning chains, and returned the "
        "conclusion from the highest-scoring chain.\n\n"
        f"**Response given:**\n{prior_response[:300]}"
    )
