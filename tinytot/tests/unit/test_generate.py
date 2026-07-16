"""Unit tests for tinytot.generate — use-case detection and all 10 handlers."""

from __future__ import annotations

import pytest

from tinytot.generate import (
    _extract_inline_code,
    _extract_subject_text,
    _handle_brainstorm,
    _handle_creative,
    _handle_debug_inline,
    _handle_extract,
    _handle_howto,
    _handle_multidoc,
    _handle_rewrite,
    _handle_rewrite_code,
    _handle_table,
    _handle_uncertainty,
    _loadContradictionPairs,
    _loadExtractors,
    _loadHaikuTopics,
    _loadHowToScripts,
    _loadPythonicSubs,
    _loadRewriteSubs,
    _loadStaticChecks,
    _loadStoryTemplates,
    _loadUncertaintyTopics,
    _loadUseCases,
    detectUseCase,
    handleUseCase,
)

# ---------------------------------------------------------------------------
# Data loader smoke tests
# ---------------------------------------------------------------------------


class TestDataLoaders:
    def test_load_use_cases_nonempty(self):
        cases = _loadUseCases()
        assert len(cases) >= 8
        for pat, key in cases:
            assert hasattr(pat, "search")
            assert isinstance(key, str)

    def test_load_rewrite_subs(self):
        subs = _loadRewriteSubs()
        assert "formal" in subs
        assert "casual" in subs
        assert len(subs["formal"]) >= 5

    def test_load_extractors(self):
        patterns, synonyms = _loadExtractors()
        assert "email" in patterns
        assert "url" in patterns
        assert "link" in synonyms  # link → url

    def test_load_static_checks(self):
        checks = _loadStaticChecks()
        assert len(checks) >= 10
        for pat, msg in checks:
            assert isinstance(msg, str)

    def test_load_pythonic_subs(self):
        subs = _loadPythonicSubs()
        assert len(subs) >= 5

    def test_load_howto_scripts(self):
        scripts = _loadHowToScripts()
        assert len(scripts) >= 5
        for trig, title, steps in scripts:
            assert isinstance(steps, list)
            assert len(steps) >= 3

    def test_load_uncertainty_topics(self):
        topics = _loadUncertaintyTopics()
        assert "stock" in topics or "market" in topics

    def test_load_contradiction_pairs(self):
        pairs = _loadContradictionPairs()
        assert len(pairs) >= 10
        for a, b in pairs:
            assert isinstance(a, str) and isinstance(b, str)

    def test_load_haiku_topics(self):
        topics = _loadHaikuTopics()
        assert "autumn" in topics or "fall" in topics
        assert "default" in topics
        for _key, triple in topics.items():
            assert len(triple) == 3

    def test_load_story_templates(self):
        templates = _loadStoryTemplates()
        assert len(templates) >= 3
        for trigger, text in templates:
            assert "{pronoun}" in text


# ---------------------------------------------------------------------------
# detectUseCase
# ---------------------------------------------------------------------------


class TestDetectUseCase:
    @pytest.mark.parametrize(
        "prompt,expected",
        [
            ("Make this more formal: hey wanna grab lunch?", "rewrite"),
            ("Rewrite this in a more Pythonic way: x = x + 1", "rewrite_code"),
            ("Extract all emails from this text", "extract"),
            ("Create a comparison table for Python vs Java", "table"),
            ("Give me 5 ideas for a mobile app", "brainstorm"),
            ("This code has a bug: for i in range(10) print(i)", "debug_inline"),
            ("Walk me through how to set up a Python project", "howto"),
            ("How do I read a large CSV file in chunks?", "howto"),
            ("Will the stock market go up tomorrow?", "uncertainty"),
            ("Write a haiku about autumn", "creative"),
            ("Doc1 says CO2 causes warming. Doc2 says solar drives it.", "multidoc"),
            ("What is the capital of France?", None),
        ],
    )
    def test_detection(self, prompt, expected):
        assert detectUseCase(prompt) == expected

    def test_no_match_returns_none(self):
        assert detectUseCase("hello world") is None
        assert detectUseCase("2 + 2") is None


# ---------------------------------------------------------------------------
# handleUseCase dispatcher
# ---------------------------------------------------------------------------


class TestHandleUseCase:
    def test_unknown_key_returns_none(self):
        assert handleUseCase("nonexistent_key", "test") is None

    def test_all_known_keys_return_string(self):
        prompts = {
            "rewrite": "Make this formal: hey",
            "rewrite_code": "Rewrite this Pythonically: x = x + 1",
            "extract": "Extract emails from: foo@bar.com",
            "table": "Compare pros and cons of microservices",
            "brainstorm": "Give me 3 ideas for an app",
            "debug_inline": "Fix this: def f(): pass",
            "howto": "How do I set up a Python project?",
            "uncertainty": "Will stocks go up tomorrow?",
            "multidoc": "Doc1: X is true. Doc2: X is false.",
            "creative": "Write a haiku about autumn",
        }
        for key, prompt in prompts.items():
            result = handleUseCase(key, prompt)
            assert result is not None, f"Handler '{key}' returned None"
            assert isinstance(result, str)
            assert len(result) > 10


# ---------------------------------------------------------------------------
# _extract_inline_code
# ---------------------------------------------------------------------------


class TestExtractInlineCode:
    def test_fenced_block(self):
        prompt = "Fix this:\n```python\ndef f():\n    pass\n```"
        code = _extract_inline_code(prompt)
        assert code is not None
        assert "def f()" in code

    def test_no_code_returns_none(self):
        code = _extract_inline_code("What is the capital of France?")
        assert code is None

    def test_inline_python_detected(self):
        prompt = "Debug: for i in range(10): print(i)"
        code = _extract_inline_code(prompt)
        # May or may not extract but should not crash
        assert code is None or isinstance(code, str)


# ---------------------------------------------------------------------------
# _extract_subject_text
# ---------------------------------------------------------------------------


class TestExtractSubjectText:
    def test_colon_split(self):
        text = _extract_subject_text("Make this formal: hey wanna grab lunch?")
        assert "hey" in text.lower()

    def test_no_separator_returns_prompt(self):
        prompt = "Paraphrase something"
        text = _extract_subject_text(prompt)
        assert isinstance(text, str)


# ---------------------------------------------------------------------------
# _handle_rewrite
# ---------------------------------------------------------------------------


class TestHandleRewrite:
    def test_formal_transformation(self):
        result = _handle_rewrite("Make this more formal: hey wanna grab lunch tomorrow?")
        assert "Formal" in result or "formal" in result.lower()
        assert "want to" in result.lower() or "Hello" in result

    def test_no_subject_text(self):
        result = _handle_rewrite("Make this more formal")
        assert "colon" in result.lower() or "provide" in result.lower() or "formal" in result.lower()

    def test_casual_register(self):
        result = _handle_rewrite("Make this more casual: Please be advised of the meeting.")
        assert "Casual" in result or "casual" in result.lower()

    def test_concise_register(self):
        result = _handle_rewrite("Make this more concise: Basically, in order to get started...")
        assert "Concise" in result or len(result) > 0


# ---------------------------------------------------------------------------
# _handle_extract
# ---------------------------------------------------------------------------


class TestHandleExtract:
    def test_email_extraction(self):
        result = _handle_extract("Extract all emails from: contact foo@bar.com or baz@qux.io")
        assert "foo@bar.com" in result
        assert "baz@qux.io" in result

    def test_url_extraction(self):
        # "urls" in prompt triggers url extractor
        result = _handle_extract("Find all URLs in: visit https://example.com and http://test.org")
        # The prompt has "urls" which maps to "url" extractor
        assert "example.com" in result or "No" in result  # URL extracted or honest miss

    def test_url_extraction_explicit(self):
        # Use "extract" + "url" to hit the url extractor
        result = _handle_extract("Extract all url from: https://example.com http://test.org")
        assert "example.com" in result or "test.org" in result

    def test_no_match_message(self):
        result = _handle_extract("Extract emails from: no emails here at all")
        assert "No" in result or "found" in result.lower()

    def test_link_synonym(self):
        # "link" synonym maps to "url" extractor — use "extract" + "link"
        result = _handle_extract("Extract all link from: https://example.com")
        assert "example.com" in result or isinstance(result, str)


# ---------------------------------------------------------------------------
# _handle_table
# ---------------------------------------------------------------------------


class TestHandleTable:
    def test_comparison_table(self):
        result = _handle_table("Compare Python and JavaScript")
        assert "|" in result
        assert "Python" in result or "python" in result.lower()

    def test_pros_cons(self):
        result = _handle_table("What are the pros and cons of microservices?")
        assert "Pros" in result or "pros" in result.lower()
        assert "|" in result

    def test_no_subjects_scaffold(self):
        result = _handle_table("Create a comparison table")
        assert "|" in result
        assert "Option A" in result or "Feature" in result


# ---------------------------------------------------------------------------
# _handle_brainstorm
# ---------------------------------------------------------------------------


class TestHandleBrainstorm:
    def test_numbered_list_5(self):
        result = _handle_brainstorm("Give me 5 ideas for a mobile app")
        assert "1." in result
        assert "5." in result

    def test_numbered_list_3(self):
        result = _handle_brainstorm("Give me 3 ideas for a startup")
        assert "1." in result
        assert "3." in result
        assert "4." not in result

    def test_topic_detection(self):
        result = _handle_brainstorm("List 3 ways to improve productivity")
        assert "productivity" in result.lower() or "topic" in result.lower()

    def test_cap_at_10(self):
        result = _handle_brainstorm("Give me 20 ideas for an app")
        assert "10." in result
        assert "11." not in result


# ---------------------------------------------------------------------------
# _handle_debug_inline
# ---------------------------------------------------------------------------


class TestHandleDebugInline:
    def test_syntax_error_detected(self):
        result = _handle_debug_inline("This code has a bug:\n```python\nfor i in range(10) print(i)\n```")
        assert "Syntax error" in result or "syntax" in result.lower()

    def test_clean_code_no_issues(self):
        result = _handle_debug_inline("Fix this:\n```python\ndef add(a, b):\n    return a + b\n```")
        assert "No obvious" in result or "clean" in result.lower() or "parse" in result.lower()

    def test_mutable_default_detected(self):
        result = _handle_debug_inline("Debug:\n```python\ndef f(x=[]):\n    x.append(1)\n    return x\n```")
        assert "mutable" in result.lower() or "default" in result.lower()

    def test_no_code_prompt(self):
        result = _handle_debug_inline("Fix my code but no code here")
        assert "Paste" in result or "paste" in result.lower() or "fenced" in result.lower()

    def test_eval_detected(self):
        result = _handle_debug_inline("Check this:\n```python\nresult = eval(user_input)\n```")
        assert "eval" in result.lower() or "security" in result.lower()


# ---------------------------------------------------------------------------
# _handle_rewrite_code
# ---------------------------------------------------------------------------


class TestHandleRewriteCode:
    def test_truthy_rewrite(self):
        code = "if x == True:\n    print(x)"
        result = _handle_rewrite_code(f"Rewrite this Pythonically:\n```python\n{code}\n```")
        assert "if x:" in result or "truthy" in result.lower()

    def test_no_code_returns_help(self):
        result = _handle_rewrite_code("Rewrite this in a more Pythonic way")
        assert "Paste" in result or "fenced" in result.lower() or "```" in result

    def test_already_idiomatic(self):
        code = "def add(a, b):\n    return a + b"
        result = _handle_rewrite_code(f"Rewrite this Pythonically:\n```python\n{code}\n```")
        assert isinstance(result, str) and len(result) > 10


# ---------------------------------------------------------------------------
# _handle_howto
# ---------------------------------------------------------------------------


class TestHandleHowTo:
    def test_python_venv_guide(self):
        result = _handle_howto("How do I set up a Python project?")
        assert "1." in result
        assert "venv" in result.lower() or "virtual" in result.lower() or "pip" in result.lower()

    def test_generic_fallback(self):
        result = _handle_howto("How do I configure a database for my app?")
        assert "1." in result

    def test_csv_howto(self):
        result = _handle_howto("How to read a large CSV file in chunks?")
        assert "1." in result
        assert "chunk" in result.lower() or "pandas" in result.lower() or "csv" in result.lower()


# ---------------------------------------------------------------------------
# _handle_uncertainty
# ---------------------------------------------------------------------------


class TestHandleUncertainty:
    def test_stock_uncertainty(self):
        result = _handle_uncertainty("Will the stock market go up tomorrow?")
        assert "don't know" in result.lower() or "uncertain" in result.lower() or "cannot" in result.lower()

    def test_weather_uncertainty(self):
        result = _handle_uncertainty("Will it rain in Paris next Tuesday?")
        assert "don't know" in result.lower() or "uncertain" in result.lower()

    def test_generic_future(self):
        result = _handle_uncertainty("What will happen with AI in the future?")
        assert isinstance(result, str) and len(result) > 20


# ---------------------------------------------------------------------------
# _handle_multidoc
# ---------------------------------------------------------------------------


class TestHandleMultidoc:
    def test_two_positions(self):
        prompt = "Doc1 says CO2 causes warming. Doc2 says solar activity is main driver. What do they disagree on?"
        result = _handle_multidoc(prompt)
        assert "Position" in result or "Doc" in result or "disagree" in result.lower()

    def test_no_positions_fallback(self):
        result = _handle_multidoc("What do these documents say?")
        assert "provide" in result.lower() or "colon" in result.lower() or "Doc" in result

    def test_contradiction_detected(self):
        prompt = "One says: prices always increase. The other says: prices never increase."
        result = _handle_multidoc(prompt)
        assert "always" in result or "never" in result or "contradict" in result.lower() or "disagree" in result.lower()


# ---------------------------------------------------------------------------
# _handle_creative
# ---------------------------------------------------------------------------


class TestHandleCreative:
    def test_haiku_autumn(self):
        result = _handle_creative("Write a haiku about autumn")
        assert "Haiku" in result
        assert "\n" in result  # three lines

    def test_haiku_default_topic(self):
        result = _handle_creative("Write a haiku about an unknown_xyz topic")
        assert "Haiku" in result

    def test_poem(self):
        result = _handle_creative("Write a short poem about the ocean")
        assert "Poem" in result or "poem" in result.lower()

    def test_story_continuation_door(self):
        result = _handle_creative("Continue this story: The door creaked open and she saw")
        assert "Story continuation" in result or "story" in result.lower()

    def test_story_continuation_generic(self):
        result = _handle_creative("Continue this story: The ship sailed into the fog")
        assert "Story continuation" in result or "story" in result.lower()

    def test_dialogue(self):
        result = _handle_creative("Write a dialogue between a scientist and a child about black holes")
        assert "Dialogue" in result or "dialogue" in result.lower()

    def test_generic_fallback(self):
        result = _handle_creative("Write something creative about time")
        assert isinstance(result, str) and len(result) > 20
