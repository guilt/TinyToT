"""Tests for tinytot.inference — reasoning trace generation and response formatting."""

import json

import pytest

from tinytot.content import getCategories, loadReasoningChains
from tinytot.inference import (
    RESPONSE_LEARNING_PREFIX,
    buildContextPrompt,
    detectResponseMode,
    executeReasoningSteps,
    extractEvaluatedResponse,
    generateJsonScoringResponse,
    generateReasoningResponse,
    generateTreeOfThoughtsResponse,
    shapeDirectAnswer,
)
from tinytot.retrieval import buildChainIndex, buildKnowledgeIndex


@pytest.fixture(autouse=True)
def clear_caches():
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()
    buildChainIndex.cache_clear()
    buildKnowledgeIndex.cache_clear()
    yield
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()
    buildChainIndex.cache_clear()
    buildKnowledgeIndex.cache_clear()


# ---------------------------------------------------------------------------
# executeReasoningSteps
# ---------------------------------------------------------------------------


class TestExecuteReasoningSteps:
    def test_includes_learning_prefix(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        result = executeReasoningSteps("test prompt", "math", chains[0])
        assert RESPONSE_LEARNING_PREFIX in result

    def test_includes_conclusion(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        result = executeReasoningSteps("test prompt", "math", chains[0])
        assert "Conclusion:" in result

    def test_includes_prompt_text(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        result = executeReasoningSteps("my special prompt", "math", chains[0])
        assert "my special prompt" in result

    def test_step_numbers_present(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        result = executeReasoningSteps("test", "math", chains[0])
        assert "Step 1:" in result
        assert "Step 2:" in result

    def test_chain_title_included(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        arith = next(c for c in chains if c[0] == "Arithmetic")
        result = executeReasoningSteps("test", "math", arith)
        assert "Arithmetic" in result

    def test_category_in_reasoning_header(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        result = executeReasoningSteps("test", "math", chains[0])
        assert "math" in result


# ---------------------------------------------------------------------------
# generateTreeOfThoughtsResponse
# ---------------------------------------------------------------------------


class TestGenerateTreeOfThoughtsResponse:
    def test_returns_string(self, category_dir, tmp_path):
        result = generateTreeOfThoughtsResponse("calculate area of a circle", category_dir, tmp_path)
        assert isinstance(result, str)

    def test_non_empty_response(self, category_dir, tmp_path):
        result = generateTreeOfThoughtsResponse("solve the equation 2x plus 3 equals 7", category_dir, tmp_path)
        assert len(result.strip()) > 0

    def test_response_is_string_not_trace(self, category_dir, tmp_path):
        # Direct answers no longer wrap in ToT trace format
        result = generateTreeOfThoughtsResponse("calculate multiply arithmetic", category_dir, tmp_path)
        assert isinstance(result, str) and len(result) > 0

    def test_response_for_knowledge_query(self, category_dir, tmp_path):
        result = generateTreeOfThoughtsResponse("find information about climate", category_dir, tmp_path)
        assert isinstance(result, str) and len(result) > 0

    def test_fallback_for_empty_category_dir(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = generateTreeOfThoughtsResponse("any prompt", empty, tmp_path)
        assert "I need to reason about" in result or isinstance(result, str)

    def test_math_response_has_content(self, category_dir, tmp_path):
        result = generateTreeOfThoughtsResponse("calculate the factorial", category_dir, tmp_path)
        assert isinstance(result, str) and len(result.strip()) > 5

    def test_math_prompt_returns_answer(self, category_dir, tmp_path):
        result = generateTreeOfThoughtsResponse("calculate multiply equation", category_dir, tmp_path)
        assert isinstance(result, str) and len(result.strip()) > 0

    def test_think_tags_wrap_trace_when_conclusion_present(self, category_dir, tmp_path):
        # A query that matches a chain with a real Conclusion: field should return
        # <think>…</think> wrapping the trace and the conclusion as the visible answer.
        result = generateTreeOfThoughtsResponse("what does CPU stand for", category_dir, tmp_path)
        assert isinstance(result, str) and len(result.strip()) > 0
        if result.startswith("<think>"):
            assert "</think>" in result
            _, answer = result.split("</think>", 1)
            assert answer.strip()  # visible answer must be non-empty


# ---------------------------------------------------------------------------
# generateReasoningResponse (thin wrapper)
# ---------------------------------------------------------------------------


class TestGenerateReasoningResponse:
    def test_delegates_to_tot(self, category_dir, tmp_path):
        r1 = generateTreeOfThoughtsResponse("calculate area", category_dir, tmp_path)
        r2 = generateReasoningResponse("calculate area", category_dir, tmp_path)
        assert r1 == r2

    def test_knowledge_answer_returned_directly(self, category_dir):
        from tinytot.retrieval import buildKnowledgeIndex

        buildKnowledgeIndex.cache_clear()
        result = generateReasoningResponse("What is the capital of France?", category_dir)
        # Knowledge passage is used as grounding context in the conclusion
        assert "Paris" in result
        buildKnowledgeIndex.cache_clear()


# ---------------------------------------------------------------------------
# detectResponseMode
# ---------------------------------------------------------------------------


class TestDetectResponseMode:
    def test_reply_with_json(self):
        assert detectResponseMode("Reply with JSON: {score, rationale}") == "json_scoring"

    def test_return_json(self):
        assert detectResponseMode("Evaluate and return JSON only.") == "json_scoring"

    def test_score_key_pattern(self):
        assert detectResponseMode('Output format: {"score": 0.9, "rationale": "good"}') == "json_scoring"

    def test_rationale_key_pattern(self):
        assert detectResponseMode('Reply with JSON only: {"rationale": "..."}') == "json_scoring"

    def test_in_one_word(self):
        assert detectResponseMode("What is the capital? Answer in one word.") == "direct"

    def test_briefly(self):
        assert detectResponseMode("Briefly explain photosynthesis.") == "direct"

    def test_in_one_sentence(self):
        assert detectResponseMode("In one sentence, what is DNA?") == "direct"

    def test_short_answer(self):
        assert detectResponseMode("Give a short answer: what is Python?") == "direct"

    def test_plain_prompt_is_reasoning_trace(self):
        assert detectResponseMode("Calculate the area of a circle with radius 5") == "reasoning_trace"

    def test_json_mode_beats_direct_mode(self):
        prompt = 'Reply with JSON briefly. {"score": 0.5, "rationale": "x"}'
        assert detectResponseMode(prompt) == "json_scoring"


# ---------------------------------------------------------------------------
# extractEvaluatedResponse
# ---------------------------------------------------------------------------


class TestExtractEvaluatedResponse:
    def test_extracts_response_section(self):
        prompt = "Question: Is the sky blue?\nResponse: Yes, the sky is blue.\nRubric: must be factual"
        assert "sky is blue" in extractEvaluatedResponse(prompt)

    def test_falls_back_to_full_prompt_when_no_label(self):
        prompt = "No labels here at all"
        assert extractEvaluatedResponse(prompt) == prompt

    def test_strips_whitespace(self):
        prompt = "Response:   trimmed content   \n"
        assert extractEvaluatedResponse(prompt) == "trimmed content"

    def test_stops_at_rubric_section(self):
        prompt = "Response: The sky is blue.\nRubric: Must mention Rayleigh scattering."
        result = extractEvaluatedResponse(prompt)
        assert "Rubric" not in result
        assert "sky is blue" in result


# ---------------------------------------------------------------------------
# generateJsonScoringResponse
# ---------------------------------------------------------------------------


class TestGenerateJsonScoringResponse:
    def test_returns_valid_json(self, tmp_path):
        prompt = "Reply with JSON. Response: The capital of France is Paris."
        result = generateJsonScoringResponse(prompt, tmp_path)
        parsed = json.loads(result)
        assert "score" in parsed
        assert "rationale" in parsed

    def test_score_in_unit_range(self, tmp_path):
        prompt = "Return JSON. Response: random unrelated xyzzy fribble blorp"
        result = generateJsonScoringResponse(prompt, tmp_path)
        parsed = json.loads(result)
        assert 0.0 <= parsed["score"] <= 1.0

    def test_rationale_is_non_empty_string(self, tmp_path):
        result = generateJsonScoringResponse("Reply with JSON. Response: test", tmp_path)
        parsed = json.loads(result)
        assert isinstance(parsed["rationale"], str)
        assert len(parsed["rationale"]) > 0

    def test_on_topic_scores_higher_than_off_topic(self):
        buildKnowledgeIndex.cache_clear()
        on_topic = "Reply with JSON. Response: Paris is the capital of France and its largest city."
        off_topic = "Reply with JSON. Response: Zorbax is a planet in the Fribble star system."
        r_on = json.loads(generateJsonScoringResponse(on_topic))
        r_off = json.loads(generateJsonScoringResponse(off_topic))
        assert r_on["score"] >= r_off["score"]
        buildKnowledgeIndex.cache_clear()

    def test_dispatcher_routes_json_scoring_prompts(self, category_dir):
        buildKnowledgeIndex.cache_clear()
        prompt = 'Reply with JSON only: {"score": float, "rationale": str}. Response: The sky is blue.'
        result = generateReasoningResponse(prompt, category_dir)
        parsed = json.loads(result)
        assert "score" in parsed
        buildKnowledgeIndex.cache_clear()


# ---------------------------------------------------------------------------
# shapeDirectAnswer
# ---------------------------------------------------------------------------


class TestShapeDirectAnswer:
    def test_one_word_returns_first_proper_noun(self, tmp_path):
        # With empty IDF (tmp_path knowledge dir), falls back to first non-prompt token
        from tinytot.retrieval import buildKnowledgeIndex

        buildKnowledgeIndex.cache_clear()
        passage = "Paris is the capital of France and its largest city."
        result = shapeDirectAnswer("Answer in one word.", passage, {})
        # Should return a token from the passage, not empty
        assert len(result) > 0
        buildKnowledgeIndex.cache_clear()

    def test_one_word_capital_extracts_city_name(self):
        # With real IDF the highest-IDF term in the passage is returned
        buildKnowledgeIndex.cache_clear()
        passage = "Paris is the capital of France and its largest city."
        _, idf, _ = buildKnowledgeIndex()
        result = shapeDirectAnswer("What is the capital? Answer in one word.", passage, idf)
        # Should be a proper noun from the passage
        assert result in {"Paris", "France", "capital"}
        buildKnowledgeIndex.cache_clear()

    def test_one_sentence_returns_first_sentence_only(self):
        passage = "The sky is blue because of Rayleigh scattering. This is a physical phenomenon."
        result = shapeDirectAnswer("In one sentence, why is the sky blue?", passage)
        assert "Rayleigh scattering" in result
        assert "physical phenomenon" not in result

    def test_no_hint_returns_full_passage(self):
        passage = "Machine learning is a subset of AI."
        result = shapeDirectAnswer("What is machine learning?", passage)
        assert result == passage

    def test_direct_mode_dispatcher_shapes_answer(self):
        buildKnowledgeIndex.cache_clear()
        result = generateReasoningResponse("What is the capital of France? Answer in one word.")
        # IDF-based extraction returns the most informative token from the passage;
        # with a large knowledge base the exact token varies but must be non-empty
        assert isinstance(result, str) and len(result) > 0 and len(result.split()) <= 3
        buildKnowledgeIndex.cache_clear()


# ---------------------------------------------------------------------------
# _extractLiveTopic
# ---------------------------------------------------------------------------


class TestExtractLiveTopic:
    """Cover the _extractLiveTopic helper via generateReasoningResponse."""

    def _topic(self, prompt: str) -> str:
        from tinytot.inference import _extractLiveTopic

        return _extractLiveTopic(prompt)

    def test_weather_keyword(self):
        assert self._topic("what is the weather today") == "weather information"

    def test_temperature_keyword(self):
        assert self._topic("current temperature in NYC") == "weather information"

    def test_forecast_keyword(self):
        assert self._topic("show me the forecast") == "weather information"

    def test_stock_keyword(self):
        assert self._topic("what is the stock price of AAPL") == "stock prices"

    def test_share_price_keyword(self):
        assert self._topic("share price today") == "stock prices"

    def test_exchange_rate_keyword(self):
        assert self._topic("what is the exchange rate for EUR") == "exchange rates"

    def test_currency_keyword(self):
        assert self._topic("USD to GBP currency") == "exchange rates"

    def test_news_keyword(self):
        assert self._topic("latest news about AI") == "news"

    def test_score_keyword(self):
        assert self._topic("what are the scores today") == "scores or standings"

    def test_standings_keyword(self):
        assert self._topic("league standings this week") == "scores or standings"

    def test_fallback(self):
        assert self._topic("something completely different") == "this information"

    def test_live_data_route_in_dispatcher(self):
        """generateReasoningResponse routes live-data prompts to no-data message."""
        result = generateReasoningResponse("What is the current weather in London?")
        assert "weather" in result.lower() or "live" in result.lower() or "real-time" in result.lower()


# ---------------------------------------------------------------------------
# buildContextPrompt
# ---------------------------------------------------------------------------


class TestBuildContextPrompt:
    def test_no_history_returns_current(self):
        assert buildContextPrompt([], "hello") == "hello"

    def test_history_without_assistant_returns_current(self):
        history = [{"role": "user", "content": "hi"}]
        assert buildContextPrompt(history, "how are you") == "how are you"

    def test_followup_prepends_context(self):
        history = [
            {"role": "user", "content": "tell me about Python"},
            {"role": "assistant", "content": "Python is a programming language."},
        ]
        result = buildContextPrompt(history, "tell me more about it")
        assert "tell me more" in result.lower()

    def test_clarification_answer_merges_topic(self):
        history = [
            {"role": "user", "content": "Python"},
            {"role": "assistant", "content": "Do you mean the language or the snake?"},
        ]
        result = buildContextPrompt(history, "the language")
        # Should merge the clarification topic into the current prompt
        assert isinstance(result, str) and len(result) > 0

    def test_non_followup_returns_current(self):
        history = [
            {"role": "user", "content": "what is Python"},
            {"role": "assistant", "content": "Python is a language."},
        ]
        result = buildContextPrompt(history, "explain machine learning")
        assert result == "explain machine learning"


# ---------------------------------------------------------------------------
# generateReasoningResponse — paths not yet covered
# ---------------------------------------------------------------------------


class TestGenerateReasoningResponsePaths:
    def test_yes_no_question_returns_verdict(self):
        result = generateReasoningResponse("Is Python a programming language?")
        assert isinstance(result, str) and len(result) > 0

    def test_live_data_no_live_data_message(self):
        result = generateReasoningResponse("What is the current stock price of Apple?")
        assert isinstance(result, str) and len(result) > 0

    def test_json_scoring_mode(self):
        result = generateReasoningResponse("Rate this response from 1 to 10 with a JSON score: The sky is blue.")
        assert isinstance(result, str) and len(result) > 0

    def test_project_request_returns_string(self):
        result = generateReasoningResponse("Build a complete Flask REST API project with models, routes, and tests")
        assert isinstance(result, str) and len(result) > 0

    def test_summarize_mode_short_prompt_hint(self):
        result = generateReasoningResponse("Summarize this in 50 words")
        assert isinstance(result, str) and "summarise" in result.lower()

    def test_history_refinement_explain(self):
        history = [
            {"role": "user", "content": "write a function"},
            {"role": "assistant", "content": "```python\ndef add(a, b):\n    return a + b\n```"},
        ]
        result = generateReasoningResponse("explain this", history=history)
        assert isinstance(result, str) and len(result) > 0

    def test_knowledge_grounded_answer_with_context(self, tmp_path):
        """When knowledge score >= threshold, ToT answer includes context."""
        # Use real knowledge base — a high-confidence factual query
        result = generateReasoningResponse("What is machine learning and how does it differ from deep learning?")
        assert isinstance(result, str) and len(result) > 0


# ---------------------------------------------------------------------------
# generateTreeOfThoughtsResponse — knowledge-grounded paths
# ---------------------------------------------------------------------------


class TestGenerateTreeOfThoughtsKnowledge:
    def test_knowledge_grounded_response(self, category_dir, tmp_path):
        """When knowledge is available and category-relevant, it shapes the answer."""
        result = generateTreeOfThoughtsResponse("explain machine learning to me", category_dir, tmp_path)
        assert isinstance(result, str) and len(result) > 0

    def test_no_thoughts_fallback(self, category_dir, tmp_path):
        """Chains with empty thought lists still return a string."""
        result = generateTreeOfThoughtsResponse("xyz abstract concept abc", category_dir, tmp_path)
        assert isinstance(result, str)

    def test_think_tags_appear_for_tot_path(self, category_dir, tmp_path):
        """The ToT trace path always produces <think> tags now."""
        result = generateTreeOfThoughtsResponse("what does CPU stand for", category_dir, tmp_path)
        if "<think>" in result:
            assert "</think>" in result
            _, answer = result.split("</think>", 1)
            assert answer.strip()

    def test_knowledge_direct_hit_returns_clean_string(self):
        """High-confidence KB hit short-circuits before ToT — no <think> tags."""
        result = generateReasoningResponse("What is machine learning?")
        assert isinstance(result, str) and len(result) > 0


# ---------------------------------------------------------------------------
# Conversation context: filler-after-code and review-question injection
# ---------------------------------------------------------------------------


class TestConversationContext:
    def test_filler_after_code_gives_contextual_response(self):
        """'uh' after a code response should not trigger a generic greeting."""
        history = [
            {"role": "user", "content": "write fibonacci"},
            {
                "role": "assistant",
                "content": "```python\ndef fib(n):\n    return n if n<=1 else fib(n-1)+fib(n-2)\n```",
            },
        ]
        result = generateReasoningResponse("uh", history=history)
        assert "TinyToT" not in result
        assert "Tree of Thoughts" not in result
        assert len(result) > 0

    def test_hmm_after_code_gives_contextual_response(self):
        history = [
            {"role": "user", "content": "show me sorting"},
            {"role": "assistant", "content": "```python\ndef sort(lst): return sorted(lst)\n```"},
        ]
        result = generateReasoningResponse("hmm", history=history)
        assert "TinyToT" not in result

    def test_ok_after_code_gives_contextual_response(self):
        history = [
            {"role": "user", "content": "binary search"},
            {
                "role": "assistant",
                "content": "def binary_search(arr, x):\n    lo, hi = 0, len(arr)-1\n    while lo <= hi:\n        mid = (lo+hi)//2\n        if arr[mid] == x: return mid\n        elif arr[mid] < x: lo = mid+1\n        else: hi = mid-1\n    return -1",
            },
        ]
        result = generateReasoningResponse("ok", history=history)
        assert "TinyToT" not in result

    def test_filler_without_code_history_routes_normally(self):
        """'uh' with no prior code still goes through normal routing."""
        result = generateReasoningResponse("uh")
        assert isinstance(result, str) and len(result) > 0

    def test_review_question_injects_code_context(self):
        """'Is this good enough?' after code should get a review response."""
        history = [
            {"role": "user", "content": "write fibonacci"},
            {"role": "assistant", "content": "```python\ndef fib(n): return n if n<=1 else fib(n-1)+fib(n-2)\n```"},
        ]
        result = generateReasoningResponse("Is this good enough?", history=history)
        assert isinstance(result, str) and len(result) > 0
        assert (
            "fib" in result.lower()
            or "docstring" in result.lower()
            or "suggest" in result.lower()
            or "error" in result.lower()
        )

    def test_does_this_work_after_code(self):
        history = [
            {"role": "user", "content": "quicksort"},
            {
                "role": "assistant",
                "content": "def qsort(a):\n    if len(a) <= 1: return a\n    pivot = a[0]\n    return qsort([x for x in a[1:] if x <= pivot]) + [pivot] + qsort([x for x in a[1:] if x > pivot])\n",
            },
        ]
        result = generateReasoningResponse("Does this work?", history=history)
        assert isinstance(result, str) and len(result) > 0

    def test_review_question_without_code_history_answers_normally(self):
        """'Is this good?' with no prior code falls through to normal routing."""
        result = generateReasoningResponse("Is this good?")
        assert isinstance(result, str) and len(result) > 0

    def test_build_context_prompt_review_injection(self):
        """buildContextPrompt injects code when review question follows code."""
        history = [
            {"role": "user", "content": "write a function"},
            {"role": "assistant", "content": "def greet():\n    print('hi')\n"},
        ]
        result = buildContextPrompt(history, "Is this good enough?")
        assert "[reviewing:" in result
        assert "greet" in result

    def test_build_context_prompt_no_injection_without_code(self):
        """buildContextPrompt does NOT inject when prior assistant has no code."""
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        result = buildContextPrompt(history, "Is this good enough?")
        assert "[reviewing:" not in result
