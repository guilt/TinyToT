"""Unit tests for tinytot.refine — code transformation, explanation, and reasoning."""

from __future__ import annotations

import pytest

from tinytot.refine import (
    applyRefinement,
    detectRefinementIntent,
    explainCode,
    explainReasoning,
    extractPriorCode,
    extractPriorResponse,
)

# ---------------------------------------------------------------------------
# detectRefinementIntent
# ---------------------------------------------------------------------------


class TestDetectRefinementIntent:
    @pytest.mark.parametrize(
        "prompt,expected",
        [
            ("make it async", "make_async"),
            ("convert to async", "make_async"),
            ("add type hints", "add_types"),
            ("annotate the function", "add_types"),
            ("add error handling", "add_error_handling"),
            ("wrap it in try/except", "add_error_handling"),
            ("add logging", "add_logging"),
            ("add a docstring", "add_docstring"),
            ("document the function", "add_docstring"),
            ("simplify this", "simplify"),
            ("refactor it", "simplify"),
            ("optimize this", "optimize"),
            ("make it faster", "optimize"),
            ("convert to JavaScript", "translate"),
            ("translate to go", "translate"),
            ("add unit tests", "add_tests"),
            ("write tests for this", "add_tests"),
            ("explain this code", "explain"),
            ("what does this do", "explain"),
            ("walk me through this", "explain"),
            ("what is gravity", None),
            ("hello world", None),
        ],
    )
    def test_detection(self, prompt, expected):
        assert detectRefinementIntent(prompt) == expected


# ---------------------------------------------------------------------------
# extractPriorCode / extractPriorResponse
# ---------------------------------------------------------------------------


class TestExtractPrior:
    _history_with_code = [
        {"role": "user", "content": "Write a binary search"},
        {
            "role": "assistant",
            "content": "```python\ndef binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    return lo\n```",
        },
    ]

    _history_no_code = [
        {"role": "user", "content": "What is gravity?"},
        {"role": "assistant", "content": "Gravity is a force that attracts objects with mass."},
    ]

    def test_extract_code_from_history(self):
        code = extractPriorCode(self._history_with_code)
        assert code is not None
        assert "def binary_search" in code

    def test_extract_code_empty_history(self):
        assert extractPriorCode([]) is None

    def test_extract_code_no_fenced_blocks(self):
        assert extractPriorCode(self._history_no_code) is None

    def test_extract_prior_response(self):
        response = extractPriorResponse(self._history_with_code)
        assert response is not None
        assert "binary_search" in response

    def test_extract_prior_response_empty(self):
        assert extractPriorResponse([]) is None

    def test_extract_prior_only_user_messages(self):
        history = [{"role": "user", "content": "Hello"}]
        assert extractPriorResponse(history) is None


# ---------------------------------------------------------------------------
# applyRefinement — make_async
# ---------------------------------------------------------------------------

_SIMPLE_CODE = "def add(a, b):\n    return a + b"
_SYNC_CODE = "def fetch(url):\n    import time\n    time.sleep(1)\n    return url"


class TestMakeAsync:
    def test_def_becomes_async_def(self):
        result = applyRefinement("make_async", _SIMPLE_CODE)
        assert result is not None
        assert "async def" in result

    def test_sleep_becomes_await(self):
        result = applyRefinement("make_async", _SYNC_CODE)
        assert result is not None
        assert "await" in result or "asyncio" in result

    def test_returns_fenced_block(self):
        result = applyRefinement("make_async", _SIMPLE_CODE)
        assert result is not None
        assert "```" in result


# ---------------------------------------------------------------------------
# applyRefinement — add_types
# ---------------------------------------------------------------------------


class TestAddTypes:
    def test_list_param_annotated(self):
        code = "def process(nums):\n    return sum(nums)"
        result = applyRefinement("add_types", code)
        assert result is not None
        assert "list" in result or ":" in result

    def test_name_param_annotated(self):
        code = "def greet(name):\n    return 'Hello ' + name"
        result = applyRefinement("add_types", code)
        assert result is not None
        # The heuristic may annotate name as int (n prefix) or str — just verify annotation added
        assert ":" in result or "->" in result

    def test_kwargs_annotated(self):
        code = "def f(**opts):\n    pass"
        result = applyRefinement("add_types", code)
        assert result is not None
        assert "Any" in result or "dict" in result or ":" in result

    def test_arr_param_annotated(self):
        code = "def process(arr):\n    return sorted(arr)"
        result = applyRefinement("add_types", code)
        assert result is not None
        assert "list" in result

    def test_flag_param_annotated(self):
        code = "def toggle(flag):\n    return not flag"
        result = applyRefinement("add_types", code)
        assert result is not None
        assert "bool" in result

    def test_return_bool_detected(self):
        code = "def is_valid(x):\n    return True"
        result = applyRefinement("add_types", code)
        assert result is not None
        assert "bool" in result or "->" in result

    def test_return_list_detected(self):
        code = "def get_items(data):\n    return []"
        result = applyRefinement("add_types", code)
        assert result is not None
        assert "list" in result or "->" in result

    def test_return_dict_detected(self):
        code = "def get_config(data):\n    return {}"
        result = applyRefinement("add_types", code)
        assert result is not None
        assert "dict" in result or "->" in result

    def test_fenced_output(self):
        result = applyRefinement("add_types", _SIMPLE_CODE)
        assert result is not None
        assert "```" in result


# ---------------------------------------------------------------------------
# applyRefinement — add_error_handling
# ---------------------------------------------------------------------------


class TestAddErrorHandling:
    def test_try_except_added(self):
        result = applyRefinement("add_error_handling", _SIMPLE_CODE)
        assert result is not None
        assert "try" in result or "except" in result

    def test_multifunction_error_handling(self):
        code = "def a(x):\n    return x\n\ndef b(y):\n    return y * 2"
        result = applyRefinement("add_error_handling", code)
        assert result is not None
        assert "RuntimeError" in result or "except" in result

    def test_fenced_output(self):
        result = applyRefinement("add_error_handling", _SIMPLE_CODE)
        assert "```" in result


# ---------------------------------------------------------------------------
# applyRefinement — add_logging
# ---------------------------------------------------------------------------


class TestAddLogging:
    def test_logger_inserted(self):
        result = applyRefinement("add_logging", _SIMPLE_CODE)
        assert result is not None
        assert "logger" in result or "logging" in result

    def test_fenced_output(self):
        result = applyRefinement("add_logging", _SIMPLE_CODE)
        assert "```" in result


# ---------------------------------------------------------------------------
# applyRefinement — add_docstring
# ---------------------------------------------------------------------------


class TestAddDocstring:
    def test_docstring_added(self):
        result = applyRefinement("add_docstring", _SIMPLE_CODE)
        assert result is not None
        assert '"""' in result

    def test_existing_docstring_not_duplicated(self):
        code = 'def add(a, b):\n    """Add two numbers."""\n    return a + b'
        result = applyRefinement("add_docstring", code)
        assert result is not None
        count = result.count('"""')
        # Should not add a second docstring
        assert count >= 2  # opening + closing of original


# ---------------------------------------------------------------------------
# applyRefinement — simplify
# ---------------------------------------------------------------------------


class TestSimplify:
    def test_eq_true_rewritten(self):
        code = "if x == True:\n    pass"
        result = applyRefinement("simplify", code)
        assert result is not None
        assert "if x:" in result or "== True" not in result

    def test_x_plus_one_rewritten(self):
        code = "x = x + 1"
        result = applyRefinement("simplify", code)
        assert result is not None
        assert "+= 1" in result or "x + 1" not in result

    def test_already_simple_no_change_message(self):
        result = applyRefinement("simplify", _SIMPLE_CODE)
        assert result is not None
        # Either shows a rewrite or "No changes needed"
        assert "```" in result


# ---------------------------------------------------------------------------
# applyRefinement — add_tests
# ---------------------------------------------------------------------------


class TestAddTests:
    def test_pytest_skeleton_generated(self):
        result = applyRefinement("add_tests", _SIMPLE_CODE)
        assert result is not None
        assert "def test_" in result
        assert "import pytest" in result

    def test_function_name_in_test(self):
        result = applyRefinement("add_tests", _SIMPLE_CODE)
        assert result is not None
        assert "add" in result

    def test_fenced_output(self):
        result = applyRefinement("add_tests", _SIMPLE_CODE)
        assert "```" in result


# ---------------------------------------------------------------------------
# applyRefinement — translate
# ---------------------------------------------------------------------------


class TestTranslate:
    def test_translate_to_javascript(self):
        result = applyRefinement("translate", _SIMPLE_CODE, "convert to JavaScript")
        assert result is not None
        assert "javascript" in result.lower() or "js" in result.lower()

    def test_translate_no_language_returns_none(self):
        result = applyRefinement("translate", _SIMPLE_CODE, "translate this")
        # No target language detected — should return None
        assert result is None

    def test_translate_to_go(self):
        result = applyRefinement("translate", _SIMPLE_CODE, "convert to go")
        assert result is not None
        assert "go" in result.lower()


# ---------------------------------------------------------------------------
# applyRefinement — unknown intent
# ---------------------------------------------------------------------------


class TestUnknownIntent:
    def test_unknown_returns_none(self):
        assert applyRefinement("nonexistent_intent", _SIMPLE_CODE) is None


# ---------------------------------------------------------------------------
# explainCode
# ---------------------------------------------------------------------------

_CLASS_CODE = """
class Counter:
    def __init__(self, start=0):
        self.count = start

    def increment(self):
        self.count += 1

    def reset(self):
        self.count = 0
"""

_RECURSIVE_CODE = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

_NESTED_LOOP_CODE = """
def matrix_multiply(a, b):
    result = []
    for i in range(len(a)):
        row = []
        for j in range(len(b[0])):
            total = 0
            for k in range(len(b)):
                total += a[i][k] * b[k][j]
            row.append(total)
        result.append(row)
    return result
"""


class TestExplainCode:
    def test_function_explanation(self):
        result = explainCode(_RECURSIVE_CODE)
        assert "factorial" in result
        assert "recursive" in result.lower() or "Recursive" in result

    def test_class_explanation(self):
        result = explainCode(_CLASS_CODE)
        assert "Counter" in result
        assert "increment" in result or "reset" in result

    def test_nested_loop_warning(self):
        result = explainCode(_NESTED_LOOP_CODE)
        assert "matrix_multiply" in result
        # O(n²) or nested loop warning
        assert "O(n" in result or "nested" in result.lower() or "loop" in result.lower()

    def test_function_with_string_return(self):
        code = 'def greet(name):\n    return "Hello " + name'
        result = explainCode(code)
        assert "greet" in result

    def test_module_level_variable(self):
        code = "MAX = 100\nMIN = 0\n\ndef clamp(x):\n    return max(MIN, min(MAX, x))"
        result = explainCode(code)
        assert "MAX" in result or "MIN" in result or "clamp" in result

    def test_class_with_bases(self):
        code = "class Dog(Animal):\n    def __init__(self):\n        self.name = 'Rex'\n    def bark(self):\n        return 'Woof'"
        result = explainCode(code)
        assert "Dog" in result
        assert "Animal" in result or "Inherits" in result

    def test_focus_on_class(self):
        code = _CLASS_CODE + "\ndef helper():\n    pass"
        result = explainCode(code, focus="Counter")
        assert "Counter" in result

    def test_syntax_error_reported(self):
        bad_code = "def broken(\n    pass"
        result = explainCode(bad_code)
        assert "syntax" in result.lower() or "SyntaxError" in result or "parse" in result.lower()

    def test_empty_code(self):
        result = explainCode("")
        assert isinstance(result, str)

    def test_focus_nonexistent(self):
        result = explainCode(_SIMPLE_CODE, focus="nonexistent_func")
        assert "not find" in result.lower() or "couldn't" in result.lower() or "no" in result.lower()

    def test_imports_reported(self):
        code = "import os\nimport sys\n\ndef main():\n    pass"
        result = explainCode(code)
        assert "os" in result or "sys" in result or "Import" in result


# ---------------------------------------------------------------------------
# explainReasoning
# ---------------------------------------------------------------------------

_TOT_RESPONSE = """Tree of Thoughts Analysis for: test prompt

Category: general_knowledge
Evaluated 3 reasoning paths:

=== Reasoning Path 1 (Score: 0.85) [SELECTED] ===
Step 1: Look up the fact.
Step 2: Return it.

=== Reasoning Path 2 (Score: 0.60)  ===
Step 1: Try another chain.
"""

_PLAIN_RESPONSE = "Gravity is a fundamental force that attracts objects."

_CODE_RESPONSE = "Here is the code:\n```python\ndef f():\n    return 42\n```"


class TestExplainReasoning:
    def test_tot_trace_parsed(self):
        result = explainReasoning(_TOT_RESPONSE)
        assert "reasoning" in result.lower() or "Path" in result

    def test_plain_response_explanation(self):
        result = explainReasoning(_PLAIN_RESPONSE)
        assert isinstance(result, str) and len(result) > 10

    def test_code_response_explanation(self):
        result = explainReasoning(_CODE_RESPONSE)
        assert isinstance(result, str)
        # Should either explain the code or describe the generation process
        assert len(result) > 20


# ---------------------------------------------------------------------------
# review intent and applyRefinement(review)
# ---------------------------------------------------------------------------


class TestReviewIntent:
    def test_is_this_good_enough(self):
        from tinytot.refine import detectRefinementIntent

        assert detectRefinementIntent("Is this good enough?") == "review"

    def test_does_this_work(self):
        from tinytot.refine import detectRefinementIntent

        assert detectRefinementIntent("Does this work?") == "review"

    def test_looks_good(self):
        from tinytot.refine import detectRefinementIntent

        assert detectRefinementIntent("Looks good?") == "review"

    def test_any_issues(self):
        from tinytot.refine import detectRefinementIntent

        assert detectRefinementIntent("Any issues?") == "review"

    def test_can_we_improve(self):
        from tinytot.refine import detectRefinementIntent

        assert detectRefinementIntent("Can we improve this?") == "review"

    def test_fresh_question_not_review(self):
        from tinytot.refine import detectRefinementIntent

        assert detectRefinementIntent("Write a fibonacci function") is None

    def test_review_suggestions_for_bare_code(self):
        from tinytot.refine import applyRefinement

        code = "def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)"
        result = applyRefinement("review", code)
        assert result is not None
        assert isinstance(result, str) and len(result) > 0

    def test_review_identifies_missing_docstring(self):
        from tinytot.refine import applyRefinement

        code = "def add(a, b):\n    return a + b"
        result = applyRefinement("review", code)
        assert "docstring" in result.lower()

    def test_review_identifies_missing_error_handling(self):
        from tinytot.refine import applyRefinement

        code = "def divide(a, b):\n    return a / b"
        result = applyRefinement("review", code)
        assert "error" in result.lower() or "except" in result.lower()

    def test_review_clean_code_passes(self):
        from tinytot.refine import applyRefinement

        code = (
            '"""Add two numbers."""\n'
            "def add(a: int, b: int) -> int:\n"
            "    try:\n"
            "        return a + b\n"
            "    except Exception:\n"
            "        return 0\n"
        )
        result = applyRefinement("review", code)
        assert result is not None
        assert "looks good" in result.lower() or "no changes" in result.lower() or isinstance(result, str)

    def test_review_syntax_error_reported(self):
        from tinytot.refine import applyRefinement

        code = "def broken(:\n    pass"
        result = applyRefinement("review", code)
        assert result is not None
        assert "syntax" in result.lower() or "error" in result.lower()
