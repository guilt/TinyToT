"""
tinytot.compute — Safe arithmetic, unit conversion, date reasoning, and word-problem solver.

Uses the ast module for expression parsing. Never calls eval() or exec().
All domain-specific content (names, comparatives, …) loads from data/generate/*.yaml.
"""

from __future__ import annotations

import ast
import math
import re
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Optional

from tinytot.content import DATA_DIR as _TINYTOT_DATA_DIR

_GENERATE_DATA = _TINYTOT_DATA_DIR / "generate"

__all__ = ["detectComputePrompt", "solveCompute"]

# ---------------------------------------------------------------------------
# Word-to-number mapping
# ---------------------------------------------------------------------------

_WORD_NUMBERS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "thousand": 1000,
    "million": 1000000,
}

_WORD_NUMBER_RE = re.compile(
    r"\b(" + "|".join(sorted(_WORD_NUMBERS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def _replaceWordNumbers(text: str) -> str:
    """Replace English number words with their numeric equivalents."""
    # Replace multiplier words first
    text = re.sub(r"\btwice\b", "2 times", text, flags=re.IGNORECASE)
    text = re.sub(r"\bthrice\b", "3 times", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdouble\b", "2 times", text, flags=re.IGNORECASE)
    text = re.sub(r"\btriple\b", "3 times", text, flags=re.IGNORECASE)
    text = re.sub(r"\bhalf\s+(?:of\s+)?(?=\d)", "0.5 * ", text, flags=re.IGNORECASE)

    def _sub(m: re.Match) -> str:
        return str(_WORD_NUMBERS[m.group(1).lower()])

    replaced = _WORD_NUMBER_RE.sub(_sub, text)

    # Collapse adjacent numeral pairs: "20 7" → "27"
    def _merge(m: re.Match) -> str:
        a, b = int(m.group(1)), int(m.group(2))
        if a in (20, 30, 40, 50, 60, 70, 80, 90) and 1 <= b <= 9:
            return str(a + b)
        return m.group(0)

    replaced = re.sub(r"\b(\d+)\s+(\d+)\b", _merge, replaced)
    return replaced


# ---------------------------------------------------------------------------
# Safe AST arithmetic evaluator
# ---------------------------------------------------------------------------

# Allowed AST node types for the evaluator.
_SAFE_BINOPS: dict[type, object] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a**b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
}

_SAFE_UNARYOPS: dict[type, object] = {
    ast.USub: lambda a: -a,
    ast.UAdd: lambda a: +a,
}

# sqrt(x) and factorial(x) as function call names accepted by the evaluator.
_SAFE_FUNCS: dict[str, object] = {
    "sqrt": math.sqrt,
    "factorial": math.factorial,
    "abs": abs,
}

_MAX_EXPONENT = 100  # guard against combinatorial explosion
_MAX_FACTORIAL_ARG = 20  # guard against absurdly large factorials


class _UnsafeNodeError(ValueError):
    """Raised when an AST node is not in the safe whitelist."""


def _evalNode(node: ast.AST) -> float:
    """Recursively evaluate a whitelisted AST expression node."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise _UnsafeNodeError(f"Unsupported constant type: {type(node.value)}")

    if isinstance(node, ast.BinOp):
        op_fn = _SAFE_BINOPS.get(type(node.op))
        if op_fn is None:
            raise _UnsafeNodeError(f"Unsupported binary operator: {type(node.op)}")
        left = _evalNode(node.left)
        right = _evalNode(node.right)
        if isinstance(node.op, ast.Pow):
            if abs(right) > _MAX_EXPONENT:
                raise _UnsafeNodeError("Exponent too large")
        if isinstance(node.op, ast.Div) and right == 0:
            raise ZeroDivisionError("Division by zero")
        return op_fn(left, right)

    if isinstance(node, ast.UnaryOp):
        op_fn = _SAFE_UNARYOPS.get(type(node.op))
        if op_fn is None:
            raise _UnsafeNodeError(f"Unsupported unary operator: {type(node.op)}")
        return op_fn(_evalNode(node.operand))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise _UnsafeNodeError("Only simple function names are allowed")
        fn = _SAFE_FUNCS.get(node.func.id)
        if fn is None:
            raise _UnsafeNodeError(f"Unsupported function: {node.func.id}")
        if len(node.args) != 1 or node.keywords:
            raise _UnsafeNodeError("Functions accept exactly one positional argument")
        arg = _evalNode(node.args[0])
        if node.func.id == "factorial":
            if not float(arg).is_integer() or arg < 0 or arg > _MAX_FACTORIAL_ARG:
                raise _UnsafeNodeError("factorial argument must be a non-negative integer <= 20")
            return float(math.factorial(int(arg)))
        return float(fn(arg))

    if isinstance(node, ast.Expression):
        return _evalNode(node.body)

    raise _UnsafeNodeError(f"Unsupported AST node: {type(node)}")


def _safeEval(expression: str) -> Optional[float]:
    """Parse and evaluate a mathematical expression safely via AST.

    Returns the numeric result, or None if parsing or evaluation fails.
    """
    expression = expression.strip()
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return None
    try:
        return _evalNode(tree)
    except (ZeroDivisionError, _UnsafeNodeError, ValueError, OverflowError):
        return None


def _formatNumber(value: float) -> str:
    """Format a float as an integer when it is whole, otherwise as a decimal."""
    if value == float("inf") or value != value:  # inf / nan
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    # Up to 10 significant figures, strip trailing zeros.
    return f"{value:.10g}"


# ---------------------------------------------------------------------------
# Arithmetic detection and solving
# ---------------------------------------------------------------------------

# Patterns that strongly suggest a raw math expression prompt.
_MATH_EXPR_PATTERNS = [
    # Explicit question: "what is 3 + 4?", "what's 2+3", "calculate 12 * 7", "compute sqrt(9)"
    re.compile(
        r"(?:what\s+is|what's|calculate|compute|evaluate|solve|find\s+the\s+value\s+of|"
        r"what(?:'s|\s+does)\s+\w+\s+equal)\s+(.+)",
        re.IGNORECASE,
    ),
    # Pure expression: "3 + 4", "12 * 7 - 2", "2 ** 10", "sqrt(16)"
    re.compile(
        r"^\s*[\d\s()\+\-\*\/\^\.]+(?:sqrt|factorial|abs)?\s*[\d\s()\+\-\*\/\^\.]*\s*[=?]?\s*$",
        re.IGNORECASE,
    ),
    # Expression contains a function call
    re.compile(r"\b(?:sqrt|factorial|abs)\s*\(", re.IGNORECASE),
]

# Characters that indicate a math expression is present in a candidate string.
_EXPR_CHARS_RE = re.compile(r"[\d].*[\+\-\*\/\^]|[\+\-\*\/\^].*[\d]")


def _extractMathExpression(prompt: str) -> Optional[str]:
    """Try to extract a math expression from the prompt."""
    normalised = _replaceWordNumbers(prompt)

    # Replace word operators: "times" → "*", "plus" → "+", etc.
    normalised = re.sub(r"\btimes\b", "*", normalised, flags=re.IGNORECASE)
    normalised = re.sub(r"\bplus\b", "+", normalised, flags=re.IGNORECASE)
    normalised = re.sub(r"\bminus\b", "-", normalised, flags=re.IGNORECASE)
    normalised = re.sub(r"\bdivided\s+by\b", "/", normalised, flags=re.IGNORECASE)
    normalised = re.sub(r"\bmultiplied\s+by\b", "*", normalised, flags=re.IGNORECASE)
    normalised = re.sub(r"\bto\s+the\s+power\s+of\b", "**", normalised, flags=re.IGNORECASE)
    normalised = re.sub(r"\braised\s+to\s+(?:the\s+)?power\s+of\b", "**", normalised, flags=re.IGNORECASE)
    normalised = re.sub(r"\bsquared\b", "** 2", normalised, flags=re.IGNORECASE)
    normalised = re.sub(r"\bcubed\b", "** 3", normalised, flags=re.IGNORECASE)

    # "X!" → factorial(X)
    normalised = re.sub(r"\b(\d+)!", r"factorial(\1)", normalised)

    # "square root of X" → sqrt(X)
    m = re.search(r"\bsquare\s+root\s+of\s+([\d.]+)", normalised, re.IGNORECASE)
    if m:
        return f"sqrt({m.group(1)})"

    # "cube root of X" → X ** (1/3)
    m = re.search(r"\bcube\s+root\s+of\s+([\d.]+)", normalised, re.IGNORECASE)
    if m:
        return f"{m.group(1)} ** (1/3)"

    # "factorial of X" / "X factorial" → factorial(X)
    m = re.search(r"\bfactorial\s+of\s+([\d]+)", normalised, re.IGNORECASE)
    if m:
        return f"factorial({m.group(1)})"
    m = re.search(r"\b([\d]+)\s+factorial\b", normalised, re.IGNORECASE)
    if m:
        return f"factorial({m.group(1)})"

    # "what is X?", "what's X?", "calculate X", etc.
    m = re.search(
        r"(?:what\s+is|what's|calculate|compute|evaluate|solve|find\s+the\s+value\s+of)\s+"
        r"([\d\s()\+\-\*\/\*\*\.]+(?:sqrt|factorial|abs)?[\d\s()\+\-\*\/\*\*\.]*)",
        normalised,
        re.IGNORECASE,
    )
    if m:
        expr = m.group(1).strip().rstrip("?.")
        expr = expr.replace("^", "**")
        if _safeEval(expr) is not None:
            return expr

    # sqrt/factorial function call form
    m = re.search(r"\b((?:sqrt|factorial|abs)\s*\([\d\s\+\-\*\/\.\^()]+\))", normalised, re.IGNORECASE)
    if m:
        expr = m.group(1).strip().replace("^", "**")
        if _safeEval(expr) is not None:
            return expr

    # Pure bare expression
    candidate = normalised.strip().rstrip("?=. ")
    candidate = candidate.replace("^", "**")
    if re.fullmatch(r"[\d\s()\+\-\*\/\.]+", candidate) and _EXPR_CHARS_RE.search(candidate):
        if _safeEval(candidate) is not None:
            return candidate

    return None


# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------

# (from_unit_aliases, to_unit_aliases, factor, offset_from, offset_to, result_label)
# Conversion: result = (value + offset_from) * factor + offset_to
# For linear conversions offset_from = offset_to = 0.

_CONVERSIONS = [
    # Distance
    (["miles", "mile", "mi"], ["km", "kilometers", "kilometres", "kilometer"], 1.609344, 0, 0, "km"),
    (["km", "kilometers", "kilometres", "kilometer"], ["miles", "mile", "mi"], 1 / 1.609344, 0, 0, "miles"),
    (["meters", "meter", "metres", "metre", "m"], ["feet", "foot", "ft"], 3.28084, 0, 0, "feet"),
    (["feet", "foot", "ft"], ["meters", "meter", "metres", "metre", "m"], 0.3048, 0, 0, "meters"),
    (["inches", "inch", "in"], ["centimeters", "centimetres", "cm"], 2.54, 0, 0, "cm"),
    (["centimeters", "centimetres", "cm"], ["inches", "inch", "in"], 1 / 2.54, 0, 0, "inches"),
    (["yards", "yard", "yd"], ["meters", "meter", "metres", "metre", "m"], 0.9144, 0, 0, "meters"),
    # Mass / weight
    (["kg", "kilograms", "kilogram", "kilos", "kilo"], ["pounds", "pound", "lbs", "lb"], 2.20462, 0, 0, "pounds"),
    (["pounds", "pound", "lbs", "lb"], ["kg", "kilograms", "kilogram", "kilos", "kilo"], 0.453592, 0, 0, "kg"),
    (["grams", "gram", "g"], ["ounces", "ounce", "oz"], 0.035274, 0, 0, "ounces"),
    (["ounces", "ounce", "oz"], ["grams", "gram", "g"], 28.3495, 0, 0, "grams"),
    # Temperature (special: offset-based)
    # C→F: (C * 9/5) + 32
    (["celsius", "centigrade", "°c", "c"], ["fahrenheit", "°f", "f"], 9 / 5, 0, 32, "°F"),
    # F→C: (F - 32) * 5/9  ⟹ offset_from=-32, factor=5/9, offset_to=0
    (["fahrenheit", "°f", "f"], ["celsius", "centigrade", "°c", "c"], 5 / 9, -32, 0, "°C"),
    # C→K: C + 273.15
    (["celsius", "centigrade", "°c", "c"], ["kelvin", "k"], 1, 273.15, 0, "K"),
    # K→C: K - 273.15
    (["kelvin", "k"], ["celsius", "centigrade", "°c", "c"], 1, -273.15, 0, "°C"),
    # Time
    (["hours", "hour", "hrs", "hr"], ["minutes", "minute", "mins", "min"], 60, 0, 0, "minutes"),
    (["minutes", "minute", "mins", "min"], ["hours", "hour", "hrs", "hr"], 1 / 60, 0, 0, "hours"),
    (["hours", "hour", "hrs", "hr"], ["seconds", "second", "secs", "sec"], 3600, 0, 0, "seconds"),
    (["seconds", "second", "secs", "sec"], ["hours", "hour", "hrs", "hr"], 1 / 3600, 0, 0, "hours"),
    (["days", "day"], ["hours", "hour", "hrs", "hr"], 24, 0, 0, "hours"),
    (["days", "day"], ["seconds", "second", "secs", "sec"], 86400, 0, 0, "seconds"),
    (["weeks", "week", "wks", "wk"], ["days", "day"], 7, 0, 0, "days"),
    # Speed
    (["mph", "miles per hour"], ["kph", "km/h", "kmh", "kilometers per hour"], 1.609344, 0, 0, "km/h"),
    (["kph", "km/h", "kmh", "kilometers per hour"], ["mph", "miles per hour"], 1 / 1.609344, 0, 0, "mph"),
    # Volume
    (["liters", "litres", "liter", "litre", "l"], ["gallons", "gallon", "gal"], 0.264172, 0, 0, "gallons"),
    (["gallons", "gallon", "gal"], ["liters", "litres", "liter", "litre", "l"], 3.78541, 0, 0, "liters"),
]

# "X <from_unit> to <to_unit>" or "convert X <from_unit> to <to_unit>"
_CONVERT_RE = re.compile(
    r"(?:convert\s+|how\s+many\s+\w+\s+(?:are\s+)?in\s+)?(-?[\d,]+(?:\.\d+)?)\s+([\w/°\s]+?)\s+(?:to|in(?:to)?|in)\s+([\w/°\s]+)",
    re.IGNORECASE,
)


def _solveUnitConversion(prompt: str) -> Optional[str]:
    """Detect and solve unit-conversion queries. Returns answer string or None."""
    m = _CONVERT_RE.search(_replaceWordNumbers(prompt))
    if not m:
        return None

    raw_value = m.group(1).replace(",", "")
    from_unit = m.group(2).strip().lower()
    to_unit = m.group(3).strip().lower().rstrip("?.! ")

    try:
        value = float(raw_value)
    except ValueError:
        return None

    for from_aliases, to_aliases, factor, off_from, off_to, label in _CONVERSIONS:
        if from_unit in from_aliases and to_unit in to_aliases:
            result = (value + off_from) * factor + off_to
            return f"{_formatNumber(result)} {label}"

    return None


# ---------------------------------------------------------------------------
# Date / time reasoning
# ---------------------------------------------------------------------------

_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%B %d %Y",
    "%d %B %Y",
]

_DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

# Ordinal suffix normaliser: "3rd" → "3", "21st" → "21"
_ORDINAL_RE = re.compile(r"\b(\d+)(?:st|nd|rd|th)\b", re.IGNORECASE)


def _parseDate(text: str) -> Optional[date]:
    """Attempt to parse a date string in several common formats."""
    text = _ORDINAL_RE.sub(r"\1", text).strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


# Patterns for date reasoning queries.
_DAYS_BETWEEN_RE = re.compile(
    r"(?:how\s+many\s+days?\s+(?:are\s+)?(?:between|from|since|until|to)\s+)"
    r"(.+?)\s+(?:and|to)\s+(.+?)(?:\?|$)",
    re.IGNORECASE,
)

_DAY_OF_WEEK_RE = re.compile(
    r"(?:what\s+(?:day|day\s+of\s+the\s+week)\s+(?:is|was)\s+|"
    r"which\s+day\s+(?:is|was)\s+)(.+?)(?:\?|$)",
    re.IGNORECASE,
)

_ADD_DAYS_RE = re.compile(
    r"(?:what\s+(?:date|day)\s+is\s+)?(\d+)\s+days?\s+(?:after|from|before|prior\s+to)\s+(.+?)(?:\?|$)",
    re.IGNORECASE,
)


def _solveDateReasoning(prompt: str) -> Optional[str]:
    """Detect and solve date/time queries. Returns answer string or None."""
    # "how many days between DATE1 and DATE2"
    m = _DAYS_BETWEEN_RE.search(prompt)
    if m:
        d1 = _parseDate(m.group(1).strip())
        d2 = _parseDate(m.group(2).strip())
        if d1 and d2:
            diff = abs((d2 - d1).days)
            return f"{diff} days"

    # "what day of the week is DATE"
    m = _DAY_OF_WEEK_RE.search(prompt)
    if m:
        d = _parseDate(m.group(1).strip())
        if d:
            return _DAYS_OF_WEEK[d.weekday()]

    # "X days after/before DATE"
    m = _ADD_DAYS_RE.search(prompt)
    if m:
        try:
            n = int(m.group(1))
        except ValueError:
            return None
        raw_date = m.group(2).strip()
        direction = "after" if re.search(r"\bafter\b|\bfrom\b", prompt, re.IGNORECASE) else "before"
        d = _parseDate(raw_date)
        if d:
            delta = timedelta(days=n if direction == "after" else -n)
            result = d + delta
            return result.strftime("%B %d, %Y").replace(" 0", " ")

    return None


# ---------------------------------------------------------------------------
# Word problem solver
# ---------------------------------------------------------------------------

# Sentence-level word-problem patterns.
# Group names: subj, val, rel, rval, question
_WORD_PROBLEM_PATTERNS = [
    # "Alice has 10. Bob has 3 more than Alice. How many does Bob have?"
    re.compile(
        r"(?P<subj>\w+)\s+has\s+(?P<val>[\d]+)(?:\s+\w+)?[.!]\s*"
        r"(?P<rel_subj>\w+)\s+has\s+(?P<rval>[\d]+)\s+(?P<rel>more|less|fewer)\s+(?:than\s+\w+)?[.!]",
        re.IGNORECASE,
    ),
    # "Alice has 10. Bob has 3 times as many as Alice."
    re.compile(
        r"(?P<subj>\w+)\s+has\s+(?P<val>[\d]+)(?:\s+\w+)?[.!]\s*"
        r"(?P<rel_subj>\w+)\s+has\s+(?P<rval>[\d]+)\s+times",
        re.IGNORECASE,
    ),
    # "There are X apples and Y oranges. How many are there in total?"
    re.compile(
        r"(?:there\s+are\s+|has?\s+|have\s+)?(?P<val1>[\d]+)\s+(?P<item1>\w+)\s+and\s+"
        r"(?P<val2>[\d]+)\s+(?P<item2>\w+)[.!,]?\s*how\s+many",
        re.IGNORECASE,
    ),
]

# "A has X. B has Y more/less/times. How many does B have / total?"
_SIMPLE_WORD_PROBLEM_RE = re.compile(
    r"(\w+)\s+(?:has|have|had)\s+(\d+)\s*(?:[\w\s]+?)?[.,!]?\s*"
    r"(\w+)\s+(?:has|have|had)\s+(\d+)\s+"
    r"(more|less|fewer|times(?:\s+as\s+many)?)\s*(?:than\s+\w+)?[.,!]?\s*"
    r"(?:how\s+many\s+(?:does\s+\3\s+have|(?:do\s+they\s+have\s+)?in\s+total|are\s+there\s+in\s+total|total|altogether))?",
    re.IGNORECASE,
)

_TOTAL_QUESTION_RE = re.compile(r"\b(?:total|in\s+total|altogether|combined|together)\b", re.IGNORECASE)


def _solveWordProblem(prompt: str) -> Optional[str]:
    """Pattern-match simple 1-2-step word problems. Returns answer or None."""
    normalised = _replaceWordNumbers(prompt)

    # Pattern: "X and Y together" or "X apples and Y oranges. How many total?"
    m = re.search(
        r"(?:has?\s+|have\s+|are\s+)?(\d+)\s+(?:\w+\s+)?and\s+(\d+)\s+(?:\w+\s+)?"
        r"(?:more\s+)?(?:how\s+many|what\s+(?:is\s+the\s+total|are\s+the\s+total)|total|in\s+total|altogether)",
        normalised,
        re.IGNORECASE,
    )
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return str(a + b)

    # 3-entity chain (must be checked BEFORE 2-entity to avoid partial match):
    # "A has X. B has Y times/more/less [than A]. C has Z fewer/more/times [than B]."
    # Resolve sequentially: compute B from A, then C from B.
    chain = re.search(
        r"(\w+)\s+(?:has|have|had)\s+(\d+(?:\.\d+)?)[^.!]*[.!]\s*"
        r"(\w+)\s+(?:has|have|had)\s+(\d+(?:\.\d+)?)\s+(times(?:\s+as\s+many)?|more|less|fewer)[^.!]*[.!]\s*"
        r"(\w+)\s+(?:has|have|had)\s+(\d+(?:\.\d+)?)\s+(times(?:\s+as\s+many)?|more|less|fewer)",
        normalised,
        re.IGNORECASE,
    )
    if chain:
        a_val = float(chain.group(2))
        b_delta = float(chain.group(4))
        b_rel = chain.group(5).lower()
        c_delta = float(chain.group(7))
        c_rel = chain.group(8).lower()

        if b_rel.startswith("times"):
            b_val = a_val * b_delta
        elif b_rel == "more":
            b_val = a_val + b_delta
        elif b_rel in ("less", "fewer"):
            b_val = a_val - b_delta
        else:
            return None

        if c_rel.startswith("times"):
            c_val = b_val * c_delta
        elif c_rel == "more":
            c_val = b_val + c_delta
        elif c_rel in ("less", "fewer"):
            c_val = b_val - c_delta
        else:
            return None

        is_total = bool(_TOTAL_QUESTION_RE.search(normalised))
        if is_total:
            return _formatNumber(a_val + b_val + c_val)
        return _formatNumber(c_val)

    # Pattern: "A has X. B has Y more/less/times. How many does B have / total?"
    m = re.search(
        r"(\w+)\s+(?:has|have|had)\s+(\d+)[^.!]*[.!]\s*"
        r"(\w+)\s+(?:has|have|had)\s+(\d+)\s+"
        r"(more|less|fewer|times(?:\s+as\s+many)?)",
        normalised,
        re.IGNORECASE,
    )
    if m:
        a_val = int(m.group(2))
        b_delta = int(m.group(4))
        rel = m.group(5).lower()
        is_total = bool(_TOTAL_QUESTION_RE.search(normalised))

        if rel in ("more",):
            b_val = a_val + b_delta
        elif rel in ("less", "fewer"):
            b_val = a_val - b_delta
        elif rel.startswith("times"):
            b_val = a_val * b_delta
        else:
            return None

        if is_total:
            return str(a_val + b_val)
        return str(b_val)

    # Pattern: "A has X. B has Y. How many in total?"
    m = re.search(
        r"(\w+)\s+(?:has|have|had)\s+(\d+)[^.!]*[.!]\s*"
        r"(\w+)\s+(?:has|have|had)\s+(\d+)[^.!]*[.!]",
        normalised,
        re.IGNORECASE,
    )
    if m and _TOTAL_QUESTION_RE.search(normalised):
        a_val = int(m.group(2))
        b_val = int(m.group(4))
        return str(a_val + b_val)

    # Multi-leg distance: "60km/h for 2 hours then 80km/h for 3 hours" or shorthand "60km/h 2h then 80km/h 1h"
    legs = re.findall(
        r"(\d+(?:\.\d+)?)\s*(?:mph|km/h|kmh|kph|miles?\s+per\s+hour|km\s+per\s+hour)"
        r"[^.]*?(?:for\s+)?(\d+(?:\.\d+)?)\s*h(?:ours?)?",
        normalised,
        re.IGNORECASE,
    )
    if len(legs) >= 2:
        total = sum(float(r) * float(t) for r, t in legs)
        return _formatNumber(total)

    # Single-leg: "60mph for 2.5 hours" or "60km/h 2h"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:mph|km/h|kmh|kph|miles?\s+per\s+hour|km\s+per\s+hour)"
        r"[^.]*?(?:for\s+)?(\d+(?:\.\d+)?)\s*h(?:ours?)?",
        normalised,
        re.IGNORECASE,
    )
    if m:
        return _formatNumber(float(m.group(1)) * float(m.group(2)))

    # Specific letter count: "How many r's in strawberry?" or "how many times does r appear in strawberry"
    m = re.search(
        r"(?:how\s+many\s+(?:times?\s+does?\s+(?:the\s+letter\s+)?)?|count\s+the\s+)"
        r"['\"]?([a-z])['\"]?(?:'?s)?\s+(?:appear\s+in|are\s+(?:in|there\s+in)|in)\s+(?:the\s+word\s+)?['\"]?([a-zA-Z]+)['\"]?",
        prompt,
        re.IGNORECASE,
    )
    if m and len(m.group(1)) == 1:
        letter = m.group(1).lower()
        word = m.group(2).lower()
        return str(word.count(letter))

    # Total letter count: "How many letters in 'strawberry'?"
    m = re.search(
        r"how\s+many\s+(?:letters?|characters?)\s+(?:are\s+(?:in|there\s+in)|in)\s+(?:the\s+word\s+)?['\"]?([a-zA-Z]+)['\"]?",
        prompt,
        re.IGNORECASE,
    )
    if m:
        word = m.group(1).lower()
        return str(len(word))
    m = re.search(
        r"(\d+)\s+workers?\s+(?:finish|complete|do)\s+(?:a\s+)?job\s+in\s+(\d+(?:\.\d+)?)\s+hours?"
        r".{0,60}?(?:how\s+long|how\s+many\s+hours?).{0,30}?(\d+)\s+workers?",
        normalised,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        n1, t1, n2 = int(m.group(1)), float(m.group(2)), int(m.group(3))
        total_work = n1 * t1
        return _formatNumber(total_work / n2)

    # Pattern: "A has X. B has half as many as A. C has N more than B. Total?"
    m = re.search(
        r"(\w+)\s+has\s+(\d+)[^.!]*[.!]\s*"
        r"(\w+)\s+has\s+(?:half|0\.5)\s+as\s+many\s+(?:as\s+\w+)?[.!]\s*"
        r"(\w+)\s+has\s+(\d+)\s+more\s+than\s+\w+",
        normalised,
        re.IGNORECASE,
    )
    if m and _TOTAL_QUESTION_RE.search(normalised):
        a_val = int(m.group(2))
        b_val = a_val // 2
        c_extra = int(m.group(5))
        c_val = b_val + c_extra
        return str(a_val + b_val + c_val)
    m = re.search(
        r"(\w+)\s+is\s+(\d+)\s+years?\s+(?:older|younger)\s+than\s+(\w+)[^.]*\.\s*"
        r"\3\s+is\s+(\d+)[^.]*\.\s*how\s+old\s+(?:will\s+)?\1\s+be\s+in\s+(\d+)\s+years?",
        normalised,
        re.IGNORECASE,
    )
    if m:
        diff = int(m.group(2))
        b_age = int(m.group(4))
        future_years = int(m.group(5))
        direction = "older" if "older" in m.group(0).lower() else "younger"
        a_age = b_age + diff if direction == "older" else b_age - diff
        return str(a_age + future_years)

    return None


# ---------------------------------------------------------------------------
# Geometry solver
# ---------------------------------------------------------------------------

# Each entry: (pattern, result_label_template, compute_fn)
# The compute_fn receives the match object and returns a float result.


def _solveGeometry(prompt: str) -> Optional[str]:
    """Detect and solve geometry formula queries. Returns answer string or None."""
    normalised = _replaceWordNumbers(prompt.lower())

    # Perimeter of rectangle: "perimeter of rectangle L by W" or "perimeter of rectangle LxW"
    m = re.search(
        r"perimeter\s+of\s+(?:a\s+)?rect(?:angle)?\s+(?:with\s+)?(?:length\s+)?(\d+(?:\.\d+)?)\s*(?:by|x|and)\s*(?:width\s+)?(\d+(?:\.\d+)?)",
        normalised,
    )
    if m:
        length, width = float(m.group(1)), float(m.group(2))
        return _formatNumber(2 * (length + width))

    # Area of rectangle: "area of rectangle L by W"
    m = re.search(
        r"area\s+of\s+(?:a\s+)?rect(?:angle)?\s+(?:with\s+)?(?:length\s+)?(\d+(?:\.\d+)?)\s*(?:by|x|and)\s*(?:width\s+)?(\d+(?:\.\d+)?)",
        normalised,
    )
    if m:
        length, width = float(m.group(1)), float(m.group(2))
        return _formatNumber(length * width)

    # Area of circle: "area of circle radius R" or "area of a circle with radius R"
    m = re.search(
        r"area\s+of\s+(?:a\s+)?circle\s+(?:with\s+)?(?:(?:radius|r)\s*(?:=\s*)?)?(\d+(?:\.\d+)?)",
        normalised,
    )
    if m:
        r = float(m.group(1))
        return _formatNumber(math.pi * r * r)

    # Circumference of circle: "circumference of circle radius R"
    m = re.search(
        r"circumference\s+of\s+(?:a\s+)?circle\s+(?:with\s+)?(?:(?:radius|r)\s*(?:=\s*)?)?(\d+(?:\.\d+)?)",
        normalised,
    )
    if m:
        r = float(m.group(1))
        return _formatNumber(2 * math.pi * r)

    # Volume of cube: "volume of cube side S" or "volume of a cube with side S"
    m = re.search(
        r"volume\s+of\s+(?:a\s+)?cube\s+(?:with\s+)?(?:(?:side|s)\s*(?:=\s*)?)?(\d+(?:\.\d+)?)",
        normalised,
    )
    if m:
        s = float(m.group(1))
        return _formatNumber(s**3)

    # Volume of sphere: "volume of sphere radius R" or "volume sphere radius R"
    m = re.search(
        r"volume\s+(?:of\s+)?(?:a\s+)?sphere\s+(?:with\s+)?(?:(?:radius|r)\s*(?:=\s*)?)?(\d+(?:\.\d+)?)",
        normalised,
        re.IGNORECASE,
    )
    if m:
        r = float(m.group(1))
        return _formatNumber((4 / 3) * math.pi * r**3)

    # Hypotenuse: "hypotenuse of right triangle legs A and B"
    m = re.search(
        r"hypotenuse\s+of\s+(?:a\s+)?(?:right\s+)?triangle\s+(?:with\s+)?(?:legs?\s+)?(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)",
        normalised,
    )
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return _formatNumber(math.sqrt(a**2 + b**2))

    # Area of triangle: "area of triangle base B height H" or "area triangle base B height H"
    m = re.search(
        r"area\s+(?:of\s+)?(?:a\s+)?triangle\s*(?:with\s+)?(?:base\s+)?(\d+(?:\.\d+)?)\s*(?:and\s+)?(?:height\s+)?(\d+(?:\.\d+)?)"
        r"|triangle\s+(?:base\s+)?(\d+(?:\.\d+)?)\s*(?:and\s+|by\s+)?(?:height\s+)?(\d+(?:\.\d+)?)\s*(?:area)?",
        normalised,
        re.IGNORECASE,
    )
    if m:
        if m.group(1):
            b, h = float(m.group(1)), float(m.group(2))
        else:
            b, h = float(m.group(3)), float(m.group(4))
        return _formatNumber(0.5 * b * h)

    return None


# ---------------------------------------------------------------------------
# Algebra solver
# ---------------------------------------------------------------------------

# Multiplier words: "doubled" → 2, "tripled" → 3, "halved" → 0.5
_MULTIPLIER_WORDS: dict[str, float] = {
    "doubled": 2.0,
    "tripled": 3.0,
    "quadrupled": 4.0,
    "halved": 0.5,
}

_MULTIPLIER_RE = re.compile(r"\b(" + "|".join(_MULTIPLIER_WORDS) + r")\b", re.IGNORECASE)


def _formatAlgebraResult(value: float) -> str:
    """Format an algebra result — prefer integer when whole."""
    return _formatNumber(value)


def _solveAlgebra(prompt: str) -> Optional[str]:
    """Solve linear algebra prompts, including substitution and word variants.

    Handles:
    - ax + b = c  (and ax - b = c, b + ax = c, etc.)
    - x/a = c
    - Word variants: "doubled", "tripled", "halved"
    - Substitution: "y = expr, x = N, what is y?"
    - 2x = c  (implicit multiplication)

    Returns the solved value as a string, or None if not applicable.
    """
    normalised = prompt.strip()

    # --- Substitution: "y = <expr with x>, x = <N>" ---
    # Detect "y = 2x + 3 and x = 4" or "y = 2x + 3, x = 4"
    sub_m = re.search(
        r"\b([a-zA-Z])\s*=\s*([^,;]+?)\s*[,;]?\s*(?:and\s+)?([a-zA-Z])\s*=\s*(-?\d+(?:\.\d+)?)",
        normalised,
        re.IGNORECASE,
    )
    if sub_m:
        lhs_var = sub_m.group(1).lower()  # e.g. "y"
        rhs_expr = sub_m.group(2).strip()  # e.g. "2x + 3"
        known_var = sub_m.group(3).lower()  # e.g. "x"
        known_val = float(sub_m.group(4))  # e.g. 4.0

        # The two variables must be different.
        if lhs_var != known_var:
            # Replace known_var in rhs_expr with its numeric value.
            # Handle implicit multiplication: "2x" → "2*4"
            subst = re.sub(
                r"(\d+(?:\.\d+)?)\s*" + re.escape(known_var),
                lambda m: str(float(m.group(1)) * known_val),
                rhs_expr,
                flags=re.IGNORECASE,
            )
            # Also replace a lone variable letter: "x" alone
            subst = re.sub(
                r"(?<![a-zA-Z0-9])" + re.escape(known_var) + r"(?![a-zA-Z0-9])",
                str(known_val),
                subst,
                flags=re.IGNORECASE,
            )
            result = _safeEval(subst)
            if result is not None:
                return _formatAlgebraResult(result)

    # --- Word-problem: multiplier variants ("a number doubled plus 5 equals 17") ---
    # Normalise multiplier words to "N * <var>" form before further parsing.
    # "doubled" → "2 * n", "tripled" → "3 * n", "halved" → "0.5 * n"
    word_m = _MULTIPLIER_RE.search(normalised)
    if word_m:
        factor = _MULTIPLIER_WORDS[word_m.group(1).lower()]
        # Replace "a number <multiplier>" or just "<multiplier>" with a placeholder equation
        # Normalise: "A number doubled plus 5 equals 17" →  "2*n + 5 = 17"
        tmp = _MULTIPLIER_RE.sub(f"{factor} * n", normalised, count=1)
        tmp = re.sub(r"a\s+number\s+", "", tmp, flags=re.IGNORECASE)
        tmp = re.sub(r"\bequals?\b", "=", tmp, flags=re.IGNORECASE)
        tmp = re.sub(r"\bplus\b", "+", tmp, flags=re.IGNORECASE)
        tmp = re.sub(r"\bminus\b", "-", tmp, flags=re.IGNORECASE)
        # Now try to parse as linear equation using the general path below.
        normalised = tmp

    # Normalise "equals" to "=" and "what is X" / "X = ?" markers.
    normalised = re.sub(r"\bequals?\b", "=", normalised, flags=re.IGNORECASE)
    # "x = ?" — strip trailing "?"
    normalised = re.sub(r"=\s*\?", "=", normalised)

    # Strip trailing question / punctuation noise for the equation portion.
    # Extract the equation: look for "... = ..." pattern.
    eq_m = re.search(
        r"(-?[\d\s*/+\-.a-zA-Z]+?)\s*=\s*(-?[\d\s*/+\-.]+)",
        normalised,
    )
    if not eq_m:
        return None

    lhs_raw = eq_m.group(1).strip()
    rhs_raw = eq_m.group(2).strip()

    # Strip leading prose ("If ", "Given ", etc.) from lhs_raw so that only
    # the algebraic expression remains.  We keep the last segment that starts
    # with a digit or a single-letter variable (possibly preceded by sign/space).
    # Strategy: find the rightmost position where a digit or isolated letter starts
    # an expression-like token.
    lhs_expr_m = re.search(
        r"(?:^|(?<=\s))(-?\s*(?:\d[\d\s*/+\-.]*[a-zA-Z][\d\s*/+\-.\w]*|[a-zA-Z]\s*[\d\s*/+\-.]+|\d[\d\s*/+\-.]*|[a-zA-Z]))\s*$",
        lhs_raw,
    )
    if lhs_expr_m:
        lhs_raw = lhs_expr_m.group(1).strip()

    # Determine the variable: a single letter that appears in lhs_raw.
    # Use lookaround rather than \b so that "3x" (digit-adjacent) is also found.
    var_m = re.search(r"(?<![a-zA-Z])([a-zA-Z])(?![a-zA-Z])", lhs_raw)
    if not var_m:
        # Variable might also appear on rhs — swap sides.
        var_m = re.search(r"(?<![a-zA-Z])([a-zA-Z])(?![a-zA-Z])", rhs_raw)
        if not var_m:
            return None
        lhs_raw, rhs_raw = rhs_raw, lhs_raw

    var = var_m.group(1).lower()

    # Parse rhs as a constant.
    try:
        c = float(rhs_raw.replace(",", "").strip())
    except ValueError:
        return None

    # Normalise lhs: convert implicit coefficient "3x" → "3*x", "x/3" stays.
    # Handle "ax + b", "ax - b", "b + ax", "x/a"
    lhs = lhs_raw.strip()

    # Implicit multiplication: "3x" → "3*x"
    lhs = re.sub(
        r"(\d+(?:\.\d+)?)\s*(" + re.escape(var) + r")\b",
        r"\1*\2",
        lhs,
        flags=re.IGNORECASE,
    )

    # Division: "x/3" → var with coefficient 1/3 and offset 0
    div_m = re.fullmatch(
        r"\s*" + re.escape(var) + r"\s*/\s*(\d+(?:\.\d+)?)\s*",
        lhs,
        re.IGNORECASE,
    )
    if div_m:
        a = 1.0 / float(div_m.group(1))
        # x = c * (divisor)
        result = c / a  # i.e. c * divisor
        return _formatAlgebraResult(result)

    # Try to parse lhs as: a*var + b  or  b + a*var  or  a*var
    # We'll substitute var=0 to get b, and var=1 to get a+b, so a = f(1)-f(0).
    # This works for any linear expression in var.
    # Replace var with a numeric sentinel and evaluate.
    def _eval_with(val: float) -> Optional[float]:
        expr = re.sub(
            r"\b" + re.escape(var) + r"\b",
            f"({val})",
            lhs,
            flags=re.IGNORECASE,
        )
        return _safeEval(expr)

    b_val = _eval_with(0.0)
    one_val = _eval_with(1.0)
    if b_val is None or one_val is None:
        return None

    a_coeff = one_val - b_val  # slope
    if a_coeff == 0:
        return None  # degenerate / no variable

    # x = (c - b) / a
    result = (c - b_val) / a_coeff
    return _formatAlgebraResult(result)


# ---------------------------------------------------------------------------
# Percentage / markup solver
# ---------------------------------------------------------------------------


def _solvePercentage(prompt: str) -> Optional[str]:
    """Detect and solve percentage and markup/discount queries. Returns answer or None."""
    normalised = _replaceWordNumbers(prompt)

    # "X% of Y" — basic percentage
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*%\s+of\s+(\d+(?:\.\d+)?)",
        normalised,
        re.IGNORECASE,
    )
    if m:
        pct, base = float(m.group(1)), float(m.group(2))
        return _formatNumber(pct / 100 * base)

    # "X% markup on Y", "markup/profit of X% on Y", "Y ... X% markup/profit"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*%\s+(?:markup|profit)\s+on\s+(?:\$)?(\d+(?:\.\d+)?)"
        r"|(?:markup|profit)\s+of\s+(\d+(?:\.\d+)?)\s*%\s+on\s+(?:\$)?(\d+(?:\.\d+)?)"
        r"|\$?(\d+(?:\.\d+)?)\s*[^.]*?(\d+(?:\.\d+)?)\s*%\s+(?:markup|profit)",
        normalised,
        re.IGNORECASE,
    )
    if m:
        if m.group(1):
            pct, base = float(m.group(1)), float(m.group(2))
        elif m.group(3):
            pct, base = float(m.group(3)), float(m.group(4))
        else:
            base, pct = float(m.group(5)), float(m.group(6))
        return _formatNumber(base * (1 + pct / 100))

    # "X% discount on Y" or "discount of X% on Y"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*%\s+discount\s+on\s+(\d+(?:\.\d+)?)"
        r"|discount\s+of\s+(\d+(?:\.\d+)?)\s*%\s+on\s+(\d+(?:\.\d+)?)",
        normalised,
        re.IGNORECASE,
    )
    if m:
        pct = float(m.group(1) or m.group(3))
        base = float(m.group(2) or m.group(4))
        return _formatNumber(base * (1 - pct / 100))

    # "Y increased by X%" / "what is Y increased by X%"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s+increased\s+by\s+(\d+(?:\.\d+)?)\s*%",
        normalised,
        re.IGNORECASE,
    )
    if m:
        base, pct = float(m.group(1)), float(m.group(2))
        return _formatNumber(base * (1 + pct / 100))

    # "Y decreased by X%" / "Y reduced by X%"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s+(?:decreased|reduced)\s+by\s+(\d+(?:\.\d+)?)\s*%",
        normalised,
        re.IGNORECASE,
    )
    if m:
        base, pct = float(m.group(1)), float(m.group(2))
        return _formatNumber(base * (1 - pct / 100))

    # "X% more than Y"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*%\s+more\s+than\s+(\d+(?:\.\d+)?)",
        normalised,
        re.IGNORECASE,
    )
    if m:
        pct, base = float(m.group(1)), float(m.group(2))
        return _formatNumber(base * (1 + pct / 100))

    # "X% less than Y"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*%\s+less\s+than\s+(\d+(?:\.\d+)?)",
        normalised,
        re.IGNORECASE,
    )
    if m:
        pct, base = float(m.group(1)), float(m.group(2))
        return _formatNumber(base * (1 - pct / 100))

    return None


# ---------------------------------------------------------------------------
# Arithmetic prompt detection
# ---------------------------------------------------------------------------

# Triggers that indicate a compute-type prompt.
_COMPUTE_TRIGGER_PATTERNS = [
    re.compile(r"\b(?:calculate|compute|evaluate|solve)\b", re.IGNORECASE),
    re.compile(r"(?:what\s+is|what's)\s+[\d\w\s()^+\-*/.,]+[?=]?\s*$", re.IGNORECASE),
    re.compile(r"\b(?:sqrt|factorial|square\s+root|cube\s+root)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*[\+\-\*\/]\s*\d+", re.IGNORECASE),
    re.compile(r"\b\d+\s*\^\s*\d+", re.IGNORECASE),
    re.compile(r"\b\d+\s*\*\*\s*\d+", re.IGNORECASE),
    re.compile(r"\b\d+!", re.IGNORECASE),
    re.compile(r"\bto\s+the\s+power\s+of\b", re.IGNORECASE),
    re.compile(r"\braised\s+to\s+(?:the\s+)?power\b", re.IGNORECASE),
    re.compile(r"\b\w+\s+(?:squared|cubed)\b", re.IGNORECASE),
    re.compile(r"\b\w+\s+(?:times|plus|minus|divided\s+by|multiplied\s+by)\s+\w+", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s+\w+\s+(?:to|into)\s+\w+", re.IGNORECASE),
    re.compile(r"\bhow\s+many\s+days?\s+(?:between|from|since|until|to)\b", re.IGNORECASE),
    # Relational / logic: "taller than", "heavier than", "older than"
    re.compile(
        r"\b(?:taller|shorter|older|younger|heavier|lighter|faster|slower|bigger|smaller)\s+than\b", re.IGNORECASE
    ),
    # Contradiction: "Does X contradict Y", "Is X consistent with Y"
    re.compile(r"\b(?:contradict|consistent\s+with|contradiction)\b", re.IGNORECASE),
    # Coreference: "Who was leaving?", "Who did X?"
    re.compile(r"\bwho\s+was\s+(?:leaving|fired|hired|promoted|arrested|blamed)\b", re.IGNORECASE),
    re.compile(r"\bwho\s+(?:was|is|did|does)\s+(?:responsible|at\s+fault|to\s+blame|incompetent)\b", re.IGNORECASE),
    # Key=value struct: "Alice=85, Bob=92" or "Q1=100, Q2=150"
    re.compile(r"\b\w+\s*=\s*\d+(?:\.\d+)?(?:\s*,\s*\w+\s*=\s*\d+(?:\.\d+)?)+", re.IGNORECASE),
    # Multi-step price: "X for $N each ... Y for $M each ... total cost"
    re.compile(r"\$\s*\d+(?:\.\d+)?\s+(?:each|per)\b.*\btotal\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bfor\s+\$?\d+(?:\.\d+)?\s+each\b.*\bhow\s+much\b", re.IGNORECASE | re.DOTALL),
    # Distance/speed: "travels Xmph for Y hours"
    re.compile(r"\btravels?\s+\d+\s*(?:mph|km/h|miles?\s+per\s+hour)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:day|day\s+of\s+the\s+week)\s+(?:is|was)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s+days?\s+(?:after|before|from)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:has|have|had)\s+\d+\b.{0,120}\b(?:how\s+many|total|in\s+total|altogether)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    # word-number arithmetic: "seventeen times thirteen", "twice as many"
    re.compile(
        r"\b(?:seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|"
        r"hundred|thousand|million)\b.{0,30}\b(?:times|plus|minus|divided\s+by|multiplied\s+by)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:twice|thrice|double|triple|half)\b.{0,60}\b(?:how\s+many|total|altogether)\b", re.IGNORECASE | re.DOTALL
    ),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:mph|km/h)\s+for\s+\d+(?:\.\d+)?\s+hours?\b", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:mph|km/h).{0,30}\bthen\b.{0,30}\b\d+(?:\.\d+)?\s*(?:mph|km/h)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+many\s+(?:letters?|times?\s+does)\b.{0,30}\b\w{3,}\b", re.IGNORECASE),
    re.compile(r"\bhow\s+many\s+[a-z]['s]*\s+(?:are\s+)?in\s+\w+", re.IGNORECASE),
    re.compile(r"\bcount\s+the\s+[a-z]['s]*\s+in\b", re.IGNORECASE),
    re.compile(r"\b\d+\s+workers?\s+(?:finish|complete)\b.{0,40}\bhow\s+(?:long|many)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bhalf\s+as\s+many\b.{0,80}\btotal\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b\d+\s*%\s+(?:profit|markup)\s+on\b", re.IGNORECASE),
    re.compile(r"\bhow\s+old\s+will\b.{0,40}\bin\s+\d+\s+years?\b", re.IGNORECASE),
    # Logic / relational inference
    re.compile(r"\ball\s+\w+\s+(?:are\s+)?\w+.{0,40}\bis\s+\w+\s+\w+\?", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bno\s+\w+\s+can\s+\w+.{0,40}\bcan\s+\w+\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b\w+\s*>\s*\w+\s+and\s+\w+\s*>\s*\w+", re.IGNORECASE),
    re.compile(r"\bgreater\s+than\b.{0,30}\bgreater\s+than\b", re.IGNORECASE),
    # Geometry
    re.compile(
        r"\b(?:perimeter|area|circumference|volume|hypotenuse)\s+(?:of\s+)?(?:a\s+)?(?:rect(?:angle)?|circle|cube|sphere|triangle)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\btriangle\b.{0,20}\bbase\b.{0,10}\bheight\b", re.IGNORECASE),
    re.compile(r"\bright\s+triangle\b.{0,40}\blegs?\b", re.IGNORECASE),
    # Percentage / markup
    re.compile(r"\b\d+(?:\.\d+)?\s*%\s+(?:of|more\s+than|less\s+than|markup|discount)\b", re.IGNORECASE),
    re.compile(r"\b(?:markup|discount)\s+of\s+\d+(?:\.\d+)?\s*%\b", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s+(?:increased|decreased|reduced)\s+by\s+\d+(?:\.\d+)?\s*%", re.IGNORECASE),
    # 3-entity chain word problems
    re.compile(
        r"\b(?:has|have|had)\s+\d+\b.{0,200}\b(?:has|have|had)\s+\d+\b.{0,200}\b(?:has|have|had)\s+\d+\b",
        re.IGNORECASE | re.DOTALL,
    ),
    # Algebra
    re.compile(r"\b(?:solve\s+for|find\s+[a-zA-Z]|what\s+is\s+[a-zA-Z]\b)", re.IGNORECASE),
    re.compile(r"\bif\s+.{0,60}\bwhat\s+is\s+(?:x|y|the\s+number)\b", re.IGNORECASE),
    re.compile(r"\b(?:equation|algebra|linear)\b", re.IGNORECASE),
    re.compile(r"\b(?:doubled|tripled|quadrupled|halved)\b", re.IGNORECASE),
    re.compile(r"\b[a-zA-Z]\s*=\s*[^=].{0,80}[a-zA-Z]\s*=\s*\d", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b\d+\s*[a-zA-Z]\s*[+\-]\s*\d+\s*=\s*\d+", re.IGNORECASE),
    re.compile(r"\b\d+\s*[a-zA-Z]\s*=\s*\d+", re.IGNORECASE),
    re.compile(r"\b[a-zA-Z]\s*/\s*\d+\s*=\s*\d+", re.IGNORECASE),
    # Propositional logic: "A implies B", "if A then B", "A → B"
    re.compile(r"\b(?:implies|entails)\s+[A-Z]\b", re.IGNORECASE),
    re.compile(r"\bif\s+[A-Z]\s+(?:is\s+)?true\b", re.IGNORECASE),
    re.compile(r"\b[A-Z]\s+implies\s+[A-Z]\b"),
    # Fraction of total / "ate the rest"
    re.compile(r"\beat\s+the\s+rest\b.{0,80}\bfraction\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bfraction\s+(?:did|does|of)\b.{0,30}\beat\b", re.IGNORECASE | re.DOTALL),
    re.compile(
        r"\b(?:\d+\s+slices?|pieces?|portions?).{0,80}\brest\b.{0,80}\b(?:fraction|how\s+many|what)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    # Chained percentage: "discounted by X%, then taxed at Y%"
    re.compile(r"\bdiscounted\s+by\s+\d+.{0,60}\btaxed\s+at\s+\d+", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b\d+\s*%\s+(?:discount|off).{0,60}\b\d+\s*%\s+(?:tax|vat|markup)", re.IGNORECASE | re.DOTALL),
]


def detectComputePrompt(prompt: str) -> bool:
    """Return True if the prompt appears to be a computation request.

    Checks for arithmetic expressions, unit conversions, date reasoning,
    or simple word problems before deferring to the knowledge base.
    """
    normalised = _replaceWordNumbers(prompt)
    for pattern in _COMPUTE_TRIGGER_PATTERNS:
        if pattern.search(normalised):
            return True
    return False


@lru_cache(maxsize=1)
def _loadNamesGender() -> tuple[set, set]:
    """Load female/male name sets from data/generate/names_gender.yaml."""
    try:
        import yaml

        path = _GENERATE_DATA / "names_gender.yaml"
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return (
                {n.lower() for n in data.get("female", [])},
                {n.lower() for n in data.get("male", [])},
            )
    except Exception:
        pass
    return (set(), set())


@lru_cache(maxsize=1)
def _loadComparatives() -> list:
    """Load comparative adjectives from data/generate/comparatives.yaml."""
    try:
        import yaml

        path = _GENERATE_DATA / "comparatives.yaml"
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return [str(a) for a in data.get("adjectives", [])]
    except Exception:
        pass
    return [
        "taller",
        "shorter",
        "older",
        "younger",
        "heavier",
        "lighter",
        "faster",
        "slower",
        "bigger",
        "smaller",
        "greater",
        "higher",
        "lower",
    ]


def _subject_gender(name: str) -> str:
    """Heuristic gender hint for common names — loaded from data/generate/names_gender.yaml."""
    female, male = _loadNamesGender()
    n = name.lower()
    if n in female:
        return "f"
    if n in male:
        return "m"
    return "?"


# ---------------------------------------------------------------------------
# Main solver dispatcher
# ---------------------------------------------------------------------------


def solveCompute(prompt: str) -> Optional[str]:
    """Attempt to solve a computation request.

    Tries (in order): unit conversion → date reasoning → word problem → arithmetic.
    Unit conversion is checked first because prompts like "what is 32F in Celsius"
    would otherwise be captured as bare arithmetic ("32").
    """
    normalised = _replaceWordNumbers(prompt)

    # 1. Unit conversion (before arithmetic — "32 Fahrenheit" must not match as "32")
    answer = _solveUnitConversion(prompt)
    if answer is not None:
        return answer

    # 2. Geometry (before arithmetic — shape keywords with numbers)
    answer = _solveGeometry(prompt)
    if answer is not None:
        return answer

    # 3. Percentage / markup (before arithmetic — percent expressions)
    answer = _solvePercentage(prompt)
    if answer is not None:
        return answer

    # 4. Algebra (linear equation solver, before date reasoning)
    answer = _solveAlgebra(prompt)
    if answer is not None:
        return answer

    # 5. Date / time reasoning
    answer = _solveDateReasoning(prompt)
    if answer is not None:
        return answer

    # 6. Multi-step word problem (rate×time, price×qty, work rate) — before
    #    single-step word problem so complex patterns match first
    answer = _solveMultiStepWord(prompt)
    if answer is not None:
        return answer

    # 7. Structured data (key=value pairs — max/min/avg/sum)
    answer = _solveStructuredData(prompt)
    if answer is not None:
        return answer

    # 8. Contradiction detection
    answer = _solveContradiction(prompt)
    if answer is not None:
        return answer

    # 9. Pronoun coreference
    answer = _solveCoreference(prompt)
    if answer is not None:
        return answer

    # 10. Simple word problem (single-step)
    answer = _solveWordProblem(normalised)
    if answer is not None:
        return answer

    # 11. Logic / relational inference
    answer = _solveLogic(prompt)
    if answer is not None:
        return answer

    # 12. Arithmetic expression (last — most permissive extractor)
    expr = _extractMathExpression(normalised)
    if expr is not None:
        result = _safeEval(expr)
        if result is not None:
            return _formatNumber(result)

    return None


def _solveLogic(prompt: str) -> Optional[str]:
    """Solve logic and relational inference prompts.

    Handles:
    - Transitive comparative relations: taller/shorter/older/heavier/faster
    - Modus ponens: All X are Y. Z is X. Is Z Y?
    - Negation: No X can Y / No X are Y
    - Contradiction detection: Does statement A contradict statement B?
    - Pronoun coreference: Alice told Bob she was leaving. Who was leaving?
    """
    p = prompt.strip()

    # -----------------------------------------------------------------------
    # Transitive relations — adjectives loaded from data/generate/comparatives.yaml
    # -----------------------------------------------------------------------
    for adj in _loadComparatives():
        m = re.search(
            rf"(\w+)\s+is\s+{adj}\s+than\s+(\w+)"
            rf".{{0,40}}?(\w+)\s+is\s+{adj}\s+than\s+(\w+)"
            rf".{{0,60}}?is\s+(\w+)\s+{adj}\s+than\s+(\w+)",
            p,
            re.IGNORECASE,
        )
        if m:
            a, b1, b2, c, qa, qc = m.groups()
            if b1.lower() == b2.lower() and a.lower() == qa.lower() and c.lower() == qc.lower():
                return f"Yes. {a} is {adj} than {c} (by transitivity: {a} > {b1} > {c})."
        # Simpler: just "is A _ than C" with intermediate known
        m = re.search(
            rf"(\w+)\s+is\s+{adj}\s+than\s+(\w+).{{0,50}}?(\w+)\s+is\s+{adj}\s+than\s+(\w+)",
            p,
            re.IGNORECASE,
        )
        if m:
            a, b1, b2, c = m.groups()
            if b1.lower() == b2.lower():
                # Trying to ask which is tallest / shortest
                q = re.search(
                    r"(?:who|which)\s+is\s+(?:the\s+)?(?:tallest|shortest|oldest|youngest|heaviest|lightest|fastest|slowest)",
                    p,
                    re.IGNORECASE,
                )
                if q:
                    extremes = {
                        "tallest": a,
                        "shortest": c,
                        "oldest": a,
                        "youngest": c,
                        "heaviest": a,
                        "lightest": c,
                        "fastest": a,
                        "slowest": c,
                    }
                    for extreme, winner in extremes.items():
                        if extreme in q.group(0).lower():
                            return f"{winner}."

    # Numeric greater: "A is greater than B and B is greater than C, is A > C?"
    m = re.search(
        r"(\w+)\s*(?:>|is\s+greater\s+than)\s*(\w+)"
        r".{0,20}?(\w+)\s*(?:>|is\s+greater\s+than)\s*(\w+)"
        r".{0,30}?is\s+(\w+)\s*(?:>|greater\s+than)\s*(\w+)",
        p,
        re.IGNORECASE,
    )
    if m:
        a, b_left, b_right, c, q_left, q_right = m.groups()
        if b_left.lower() == b_right.lower() and a.lower() == q_left.lower() and c.lower() == q_right.lower():
            return "Yes"

    # -----------------------------------------------------------------------
    # Modus ponens
    # -----------------------------------------------------------------------
    m = re.search(
        r"all\s+(\w+)\s+(?:are\s+)?(\w+)[.!]\s*(\w+)\s+(?:is\s+(?:a\s+)?)?(?:are\s+)?(\w+)[.!]\s*(?:is\s+|are\s+)?(\w+)\s*(?:\w+\s+)?(?:\?|$)",
        p,
        re.IGNORECASE,
    )
    if m:
        class_, property_, subject, subj_class, q_subject = m.groups()
        if subj_class.lower() == class_.lower() and q_subject.lower() == subject.lower():
            return f"Yes. {subject} is {property_} because all {class_} are {property_}."

    # -----------------------------------------------------------------------
    # Negation
    # -----------------------------------------------------------------------
    m = re.search(
        r"no\s+(\w+)\s+can\s+(\w+)[.!]\s*(\w+)\s+is\s+(?:a\s+)?(\w+)[.!]\s*can\s+(\w+)\s+(\w+)",
        p,
        re.IGNORECASE,
    )
    if m:
        class_, verb, subject, subj_class, q_subject, q_verb = m.groups()
        if subj_class.lower() == class_.lower() and q_subject.lower() == subject.lower():
            return f"No. {subject} cannot {verb} because no {class_} can {verb}."

    m = re.search(
        r"no\s+(\w+)\s+are\s+(\S+)[.!]\s*(?:a\s+)?(\w+)\s+is\s+(?:a\s+)?(\w+)[.!]\s*is\s+(?:a\s+)?(\w+)\s+(\S+)",
        p,
        re.IGNORECASE,
    )
    if m:
        class_, property_, subject, subj_class, q_subject, q_property = m.groups()
        property_ = property_.rstrip(".!?,")
        q_property = q_property.rstrip(".!?,")
        if (
            subj_class.lower() == class_.lower()
            and q_subject.lower() == subject.lower()
            and q_property.lower() == property_.lower()
        ):
            return f"No. {subject} is not {property_} because no {class_} are {property_}."

    # -----------------------------------------------------------------------
    # Propositional logic — "A implies B, B implies C, A is true → C is true"
    # -----------------------------------------------------------------------
    # Match "A implies B and B implies C" style chains
    m = re.search(
        r"\b([A-Z])\s+implies\s+([A-Z])\b.{0,30}\b([A-Z])\s+implies\s+([A-Z])\b",
        p,
    )
    if m:
        p1, q1, p2, q2 = m.groups()
        # Build implication chain
        chain: dict[str, str] = {p1: q1, p2: q2}
        # Check if A is true
        true_m = re.search(r"\b([A-Z])\s+is\s+true\b", p)
        if true_m:
            start = true_m.group(1)
            conclusions = []
            current = start
            visited = set()
            while current in chain and current not in visited:
                visited.add(current)
                next_ = chain[current]
                conclusions.append(next_)
                current = next_
            if conclusions:
                chain_str = " → ".join([start] + conclusions)
                return (
                    f"By modus ponens: {chain_str}. "
                    f"Since {start} is true and {start} implies {conclusions[0]}, "
                    f"we conclude {conclusions[-1]} is true."
                )

    # "if A then B" style
    m = re.search(
        r"if\s+([A-Z])\s+(?:is\s+)?true.{0,30}?([A-Z])\s+is\s+(?:also\s+)?true",
        p,
        re.IGNORECASE,
    )
    if m:
        a, b = m.groups()
        # Look for a second implication
        m2 = re.search(rf"if\s+{b}\s+(?:is\s+)?true.{{0,30}}?([A-Z])\s+is\s+(?:also\s+)?true", p, re.IGNORECASE)
        if m2:
            c = m2.group(1)
            return f"By transitivity: if {a} then {b}, and if {b} then {c}. Since {a} is true, {c} is also true."
        return f"If {a} is true, then {b} is true (modus ponens)."

    return None


def _solveContradiction(prompt: str) -> Optional[str]:
    """Detect logical contradiction or consistency between two stated claims.

    Handles:
    - "Does 'All X can Y' contradict 'Z is X but cannot Y'?"
    - "Is it consistent that all A are B but C is A and not B?"
    """
    p = prompt.strip()

    if not re.search(r"\b(?:contradict|consistent|contradiction|inconsistent)\b", p, re.IGNORECASE):
        return None

    # Extract the two statements (quoted or after "Doc1"/"Statement A" markers)
    stmts = re.findall(r"['\"]([^'\"]+)['\"]", p)
    if len(stmts) < 2:
        # Try splitting on "and" / "but" when both clauses contain subjects
        stmts = re.split(
            r"\s+(?:and|but)\s+", re.sub(r"^.*?(?:contradict|consistent\s+with)\s*", "", p, flags=re.I), maxsplit=1
        )

    if len(stmts) < 2:
        return None

    s1, s2 = stmts[0].strip().lower(), stmts[1].strip().lower().rstrip("?.")

    # All X are Y + Z is X but not Y → contradiction
    m1 = re.search(r"all\s+(\w+)\s+(?:can|are)\s+(\w+)", s1)
    m2 = re.search(r"(\w+)s?\s+(?:are|is)\s+(?:\w+\s+)?(\w+)\s+(?:that\s+)?(?:cannot|can't|are\s+not|do\s+not)", s2)
    if m1 and m2:
        class1, prop1 = m1.groups()
        species, prop2 = m2.groups()
        if class1.lower().rstrip("s") == species.lower().rstrip("s") or prop1.lower() in s2:
            return (
                f"Yes, these statements contradict each other. "
                f"'{stmts[0].strip()}' asserts that all {class1} {prop1}, "
                f"but '{stmts[1].strip()}' presents a counterexample."
            )

    # Generic: if no specific pattern, note the surface conflict
    conflict_words = [
        ("all", "no"),
        ("always", "never"),
        ("every", "none"),
        ("can", "cannot"),
        ("can", "can't"),
        ("is", "is not"),
    ]
    for pos, neg in conflict_words:
        if pos in s1 and neg in s2:
            return (
                f"These statements appear to contradict each other: "
                f"one asserts '{pos}' while the other asserts '{neg}'."
            )
        if neg in s1 and pos in s2:
            return (
                f"These statements appear to contradict each other: "
                f"one asserts '{neg}' while the other asserts '{pos}'."
            )

    return "These statements appear consistent — no direct contradiction detected."


def _solveCoreference(prompt: str) -> Optional[str]:
    """Resolve simple pronoun coreference questions.

    Handles:
    - "Alice told Bob that she was leaving. Who was leaving?" → Alice
    - "The CEO fired the manager because he was incompetent. Who?" → ambiguous
    - "John gave Mary a gift. She thanked him. Who gave the gift?" → John
    """
    p = prompt.strip()

    # Must be asking "who" about a pronoun
    if not re.search(r"\bwho\b", p, re.IGNORECASE):
        return None

    # Extract subject-verb pairs from first clause
    # Pattern: <Name> <verb> <Name> that/because <pronoun> <state>
    m = re.search(
        r"(\b[A-Z][a-z]+\b)\s+(?:told|asked|informed|warned|said\s+to)\s+(\b[A-Z][a-z]+\b)"
        r"\s+that\s+(she|he)\s+was\s+(\w+)",
        p,
    )
    if m:
        subj, obj, pronoun, state = m.groups()
        # "she" most naturally refers to the subject when it follows "told Bob that she"
        referent = subj if pronoun.lower() == "she" and _subject_gender(subj) in ("f", "?") else obj
        return f"{referent} was {state}."

    # "A fired B because he/she was X" — pronoun ambiguity
    m = re.search(
        r"(?:the\s+)?(\b\w+\b)\s+(?:fired|hired|blamed|praised|promoted|demoted)\s+(?:the\s+)?(\w+)"
        r"\s+because\s+(he|she)\s+was\s+(\w+)",
        p,
    )
    if m:
        agent, patient, pronoun, quality = m.groups()
        # Most natural reading: the pronoun refers to the object (the one who WAS the quality)
        referent = patient.capitalize()
        return (
            f"Most likely {referent} was {quality} (the pronoun '{pronoun}' most naturally "
            f"refers to the object of the action). However, this sentence is grammatically "
            f"ambiguous — '{pronoun}' could also refer to {agent}."
        )

    # "John gave Mary a gift. She thanked him."
    m = re.search(
        r"(\b[A-Z][a-z]+\b)\s+gave\s+(\b[A-Z][a-z]+\b).{0,30}?"
        r"(?:who\s+gave|who\s+sent|who\s+brought)",
        p,
    )
    if m:
        giver, receiver = m.groups()
        return f"{giver} gave the gift."

    return None


def _solveStructuredData(prompt: str) -> Optional[str]:
    """Answer questions over key=value structured data in the prompt.

    Handles:
    - "Alice=85, Bob=92, Carol=78. Who has the highest score?" → Bob
    - "Sales: Q1=100, Q2=150, Q3=120. What is the average?" → 123.33
    - "Prices: A=$10, B=$25, C=$15. What is the total?" → $50
    """
    p = prompt.strip()

    # Find all key=value pairs (allow $ prefix on value)
    kv_re = re.compile(r"(\b\w[\w\s]*?)\s*=\s*\$?\s*([\d]+(?:\.\d+)?)", re.IGNORECASE)
    pairs = kv_re.findall(p)
    if not pairs:
        return None

    data = {k.strip(): float(v) for k, v in pairs}
    if len(data) < 2:
        return None

    p_lower = p.lower()

    # Highest / maximum
    if re.search(r"\b(?:highest|maximum|most|largest|greatest|best|top)\b", p_lower):
        winner = max(data, key=lambda k: data[k])
        return f"{winner} ({data[winner]:g})."

    # Lowest / minimum
    if re.search(r"\b(?:lowest|minimum|least|smallest|worst|bottom)\b", p_lower):
        loser = min(data, key=lambda k: data[k])
        return f"{loser} ({data[loser]:g})."

    # Average / mean
    if re.search(r"\b(?:average|mean|avg)\b", p_lower):
        avg = sum(data.values()) / len(data)
        return _formatNumber(avg)

    # Total / sum
    if re.search(r"\b(?:total|sum|altogether|combined)\b", p_lower):
        total = sum(data.values())
        return _formatNumber(total)

    # Rank / sorted
    if re.search(r"\b(?:rank|order|sort|ascending|descending)\b", p_lower):
        descending = "desc" in p_lower or "high" in p_lower
        ranked = sorted(data.items(), key=lambda x: x[1], reverse=descending)
        return ", ".join(f"{k}: {v:g}" for k, v in ranked)

    # Default: list all values
    return ", ".join(f"{k}={v:g}" for k, v in data.items())


def _solveMultiStepWord(prompt: str) -> Optional[str]:
    """Solve multi-step word problems involving rate × time, price × quantity.

    Handles:
    - "Train travels 60mph for 2.5h then 80mph for 1.5h. Total distance?"
    - "Apples $0.50 each, oranges $0.75 each. Buy 4 apples and 3 oranges. Total?"
    - "Work rate: A does job in 3h, B in 6h. Together, how long?"
    """
    p = prompt.strip()
    normalised = _replaceWordNumbers(p)

    # --- Pattern 1: rate × time segments (distance or work) ---
    # "travels 60mph for 2.5 hours then 80mph for 1.5 hours"
    leg_re = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:mph|km/h|km per hour|miles?\s*per\s*hour|kph)"
        r"\s+for\s+(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h\b)",
        re.IGNORECASE,
    )
    legs = leg_re.findall(normalised)
    if len(legs) >= 2:
        total_dist = sum(float(speed) * float(time) for speed, time in legs)
        total_time = sum(float(t) for _, t in legs)
        avg_speed = total_dist / total_time if total_time else 0
        if re.search(r"\btotal\s+distance\b|\bhow\s+far\b|\bdistance\b", p, re.IGNORECASE):
            return _formatNumber(total_dist)
        if re.search(r"\baverage\s+speed\b", p, re.IGNORECASE):
            return f"{_formatNumber(avg_speed)} (average speed over {_formatNumber(total_time)} hours)"
        # Default to total distance
        return _formatNumber(total_dist)

    # --- Pattern 2: price × quantity (shopping) ---
    # "apples for $0.50 each ... 4 apples ... oranges for $0.75 each ... 3 oranges"
    item_re = re.compile(
        r"(\w+)\s+(?:for\s+)?\$?\s*([\d]+(?:\.\d+)?)\s*(?:each|per\s+\w+)?",
        re.IGNORECASE,
    )
    qty_re = re.compile(
        r"(\d+)\s+(\w+)",
        re.IGNORECASE,
    )
    items = item_re.findall(normalised)
    qtys = qty_re.findall(normalised)

    if items and qtys and re.search(r"\btotal\b|\bhow\s+much\b", p, re.IGNORECASE):
        # Build price lookup
        price_map: dict[str, float] = {}
        for name, price in items:
            price_map[name.lower().rstrip("s")] = float(price)

        total = 0.0
        breakdown: list[str] = []
        for qty_str, item_name in qtys:
            qty = int(qty_str)
            base = item_name.lower().rstrip("s")
            if base in price_map:
                line_total = qty * price_map[base]
                total += line_total
                breakdown.append(f"{qty} × ${price_map[base]:g} = ${line_total:g}")

        if total > 0 and breakdown:
            return f"${total:g} ({'; '.join(breakdown)})"

    # --- Pattern 3: combined work rate ---
    # "A does job in 3 hours, B in 6 hours. Together, how long?"
    work_re = re.compile(
        r"(\w+)\s+(?:does|completes?|finishes?|can\s+do)\s+(?:the\s+)?(?:job|task|work)\s+in\s+(\d+(?:\.\d+)?)\s*(?:hours?|days?|hrs?)",
        re.IGNORECASE,
    )
    workers = work_re.findall(normalised)
    if len(workers) >= 2 and re.search(r"\btogether\b|\bcombined\b", p, re.IGNORECASE):
        combined_rate = sum(1.0 / float(t) for _, t in workers)
        if combined_rate > 0:
            together = 1.0 / combined_rate
            unit_m = re.search(r"\b(hours?|days?)\b", p, re.IGNORECASE)
            unit = unit_m.group(1) if unit_m else "hours"
            return f"{_formatNumber(together)} {unit}"

    # --- Pattern 4: fraction of total (slices/pieces with "ate the rest") ---
    # "Alice ate 3, Bob ate 4, Carol ate the rest. Total=12. Fraction Carol?"
    ate_re = re.compile(r"(\w+)\s+ate\s+(\d+)\s+(?:slices?|pieces?|portions?)?", re.IGNORECASE)
    ates = ate_re.findall(normalised)
    total_m = re.search(
        r"\b(\d+)\s+(?:slices?|pieces?|portions?)\s+total\b|\btotal\s+(?:of\s+)?(\d+)\s+(?:slices?|pieces?)",
        normalised,
        re.IGNORECASE,
    )
    rest_m = re.search(r"(\w+)\s+ate\s+the\s+rest", p, re.IGNORECASE)
    if ates and total_m and rest_m:
        total_slices = int(total_m.group(1) or total_m.group(2))
        rest_person = rest_m.group(1)
        known = sum(int(n) for _, n in ates)
        rest_amount = total_slices - known
        if rest_amount > 0 and re.search(r"\bfraction\b", p, re.IGNORECASE):
            from math import gcd

            g = gcd(rest_amount, total_slices)
            num, den = rest_amount // g, total_slices // g
            return f"{rest_person} ate {rest_amount}/{total_slices} = {num}/{den} of the pizza."
        if rest_amount > 0:
            return f"{rest_person} ate {rest_amount} slices."

    # --- Pattern 5: chained percentage (discount then tax) ---
    # "costs $120, discounted 25%, taxed 8%. Final price?"
    price_m = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:dollars?|USD)?", normalised, re.IGNORECASE)
    pcts = re.findall(r"(\d+(?:\.\d+)?)\s*%", normalised)
    ops = re.findall(r"\b(discount|off|tax|vat|markup|increase|decrease|reduc)\w*\b", p, re.IGNORECASE)

    if price_m and len(pcts) >= 2 and re.search(r"\b(?:final\s+price|total\s+cost|how\s+much|pay)\b", p, re.IGNORECASE):
        price = float(price_m.group(1))
        steps = []
        for pct_str, op in zip(pcts, ops):
            pct = float(pct_str) / 100
            op_l = op.lower()
            if any(kw in op_l for kw in ("discount", "off", "reduc", "decrease")):
                new_price = price * (1 - pct)
                steps.append(f"−{pct_str}% discount: ${price:g} × {1 - pct:g} = ${new_price:g}")
            else:  # tax / markup / increase
                new_price = price * (1 + pct)
                steps.append(f"+{pct_str}% {op_l}: ${price:g} × {1 + pct:g} = ${new_price:g}")
            price = new_price
        if steps:
            return f"${price:.2f} ({'; '.join(steps)})"

    return None
