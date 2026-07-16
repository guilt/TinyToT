"""Tests for tinytot.tools — parameter extraction, tool detection, MCP matching."""

from tinytot.tools import (
    detectInformationNeed,
    detectToolUsage,
    extractTopic,
    matchToolFromAvailable,
)

# ---------------------------------------------------------------------------
# extractTopic
# ---------------------------------------------------------------------------


class TestExtractTopic:
    def test_skips_action_words(self):
        result = extractTopic("search for climate change data")
        assert "climate" in result

    def test_skips_stop_words(self):
        result = extractTopic("find me about the quantum computing")
        assert "quantum" in result

    def test_short_prompt_falls_back_to_truncation(self):
        result = extractTopic("hi")
        assert result == "hi"

    def test_returns_at_most_five_words(self):
        result = extractTopic("search for one two three four five six seven")
        assert len(result.split()) <= 5

    def test_empty_prompt_fallback(self):
        result = extractTopic("")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# detectToolUsage
# ---------------------------------------------------------------------------


class TestDetectToolUsage:
    def test_search_prompt_detected(self, schema_file):
        name, params = detectToolUsage("search for quantum computing news", schema_file)
        assert name == "ddg-search"
        assert "query" in params

    def test_information_lookup_detected(self, schema_file):
        name, params = detectToolUsage("tell me about the Roman Empire", schema_file)
        assert name == "grokipedia"

    def test_excluded_keyword_prevents_match(self, schema_file):
        # "aws" is in exclude_keywords for sqlite
        name, _ = detectToolUsage("query the aws rds database", schema_file)
        assert name != "sqlite"

    def test_unmatched_prompt_returns_none(self, schema_file):
        name, params = detectToolUsage("hello world", schema_file)
        assert name is None
        assert params == {}

    def test_full_prompt_param_fills_correctly(self, schema_file):
        prompt = "sqlite database query select all from users"
        name, params = detectToolUsage(prompt, schema_file)
        if name == "sqlite":
            assert params.get("query") == prompt

    def test_extract_topic_param_is_non_empty(self, schema_file):
        name, params = detectToolUsage("search for machine learning papers", schema_file)
        assert name == "ddg-search"
        assert len(params.get("query", "")) > 0

    def test_missing_schema_returns_none(self, tmp_path):
        name, params = detectToolUsage("search for anything", tmp_path / "missing.md")
        assert name is None


# ---------------------------------------------------------------------------
# matchToolFromAvailable
# ---------------------------------------------------------------------------


class TestMatchToolFromAvailable:
    _TOOLS = [
        {"type": "function", "function": {"name": "ddg__search", "description": "DuckDuckGo"}},
        {"type": "function", "function": {"name": "grokipedia__lookup", "description": "Wiki"}},
        {"type": "function", "function": {"name": "filesystem__read", "description": "Files"}},
    ]

    def test_strong_match_returns_correct_tool(self):
        result = matchToolFromAvailable("ddg-search", self._TOOLS)
        assert result is not None
        assert "ddg" in result["name"]

    def test_prefix_match_fallback(self):
        result = matchToolFromAvailable("grokipedia-lookup", self._TOOLS)
        assert result is not None
        assert "grokipedia" in result["name"]

    def test_no_match_returns_none(self):
        result = matchToolFromAvailable("totally-unknown-tool", self._TOOLS)
        assert result is None

    def test_non_function_type_skipped(self):
        tools = [{"type": "other", "function": {"name": "ddg__search"}}]
        result = matchToolFromAvailable("ddg-search", tools)
        assert result is None

    def test_empty_tool_list_returns_none(self):
        assert matchToolFromAvailable("ddg-search", []) is None


# ---------------------------------------------------------------------------
# detectInformationNeed
# ---------------------------------------------------------------------------


class TestDetectInformationNeed:
    def test_question_word_triggers(self):
        assert detectInformationNeed("What is the capital of France?") is True

    def test_temporal_word_triggers(self):
        assert detectInformationNeed("Give me the latest news on AI") is True

    def test_research_word_triggers(self):
        assert detectInformationNeed("Explain how neural networks work") is True

    def test_capitalized_entity_triggers(self):
        assert detectInformationNeed("Tell me about Paris France") is True

    def test_plain_statement_no_trigger(self):
        # A plain lowercase statement with no signals
        assert detectInformationNeed("yes no maybe") is False
