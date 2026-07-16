"""Tests for tinytot.retrieval — TF-IDF index, cosine sim, categorization, ranking."""

import math

import pytest

from tinytot.content import getCategories, loadReasoningChains
from tinytot.retrieval import (
    DEFAULT_CATEGORY,
    MAX_EVALUATED_PATHS,
    buildChainIndex,
    categorizePrompt,
    chainVector,
    cosineSim,
    queryVector,
    rankChains,
    scoreChain,
    scoreResponse,
)


@pytest.fixture(autouse=True)
def clear_caches():
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()
    buildChainIndex.cache_clear()
    yield
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()
    buildChainIndex.cache_clear()


# ---------------------------------------------------------------------------
# buildChainIndex
# ---------------------------------------------------------------------------


class TestBuildChainIndex:
    def test_returns_correct_entry_count(self, category_dir):
        entries, idf, tfVecs = buildChainIndex(category_dir)
        # 2 math chains + 2 tool_calling chains
        assert len(entries) == 4
        assert len(tfVecs) == 4

    def test_idf_contains_chain_terms(self, category_dir):
        _, idf, _ = buildChainIndex(category_dir)
        assert "arithmetic" in idf or "calculate" in idf

    def test_tf_vecs_are_unit_norm(self, category_dir):
        _, _, tfVecs = buildChainIndex(category_dir)
        for vec in tfVecs:
            norm = math.sqrt(sum(v * v for v in vec.values()))
            assert abs(norm - 1.0) < 1e-6

    def test_empty_dir_returns_empty(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        entries, idf, vecs = buildChainIndex(empty)
        assert entries == []
        assert idf == {}
        assert vecs == []

    def test_cached_between_calls(self, category_dir):
        r1 = buildChainIndex(category_dir)
        r2 = buildChainIndex(category_dir)
        assert r1 is r2


# ---------------------------------------------------------------------------
# queryVector
# ---------------------------------------------------------------------------


class TestQueryVector:
    def test_empty_prompt_returns_empty(self):
        assert queryVector("", {}) == {}

    def test_short_words_filtered(self):
        idf = {"the": 1.0, "cat": 1.0}
        # "the" is 3 chars — included; "a" is 1 char — excluded by WORD_SHORT (\b\w{3,}\b)
        vec = queryVector("a the cat", idf)
        assert "the" in vec
        assert "a" not in vec

    def test_vector_is_unit_norm(self):
        idf = {"calculate": 2.0, "math": 1.5, "equation": 1.8}
        vec = queryVector("calculate the math equation", idf)
        norm = math.sqrt(sum(v * v for v in vec.values()))
        assert abs(norm - 1.0) < 1e-6

    def test_unknown_terms_use_default_idf(self):
        vec = queryVector("unknownterm", {})
        assert "unknownterm" in vec


# ---------------------------------------------------------------------------
# cosineSim
# ---------------------------------------------------------------------------


class TestCosineSim:
    def test_identical_vectors_score_one(self):
        v = {"foo": 0.6, "bar": 0.8}
        assert abs(cosineSim(v, v) - 1.0) < 1e-6

    def test_disjoint_vectors_score_zero(self):
        q = {"foo": 1.0}
        d = {"bar": 1.0}
        assert cosineSim(q, d) == 0.0

    def test_partial_overlap(self):
        q = {"foo": 1.0}
        d = {"foo": 0.6, "bar": 0.8}
        score = cosineSim(q, d)
        assert 0 < score < 1.0


# ---------------------------------------------------------------------------
# chainVector
# ---------------------------------------------------------------------------


class TestChainVector:
    def test_empty_chain_returns_empty(self):
        assert chainVector("", [], {}) == {}

    def test_unit_norm(self):
        idf = {"step": 1.0, "one": 1.0, "two": 1.0}
        vec = chainVector("Title", ["step one", "step two"], idf)
        norm = math.sqrt(sum(v * v for v in vec.values()))
        assert abs(norm - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# categorizePrompt
# ---------------------------------------------------------------------------


class TestCategorizePrompt:
    def test_math_prompt_routes_to_math(self, category_dir):
        cat = categorizePrompt("calculate the area of a circle", category_dir)
        assert cat == "math"

    def test_search_prompt_routes_to_tool_calling(self, category_dir):
        cat = categorizePrompt("search for information about climate", category_dir)
        assert cat == "tool_calling"

    def test_empty_prompt_returns_default(self, category_dir):
        cat = categorizePrompt("", category_dir)
        assert cat == DEFAULT_CATEGORY

    def test_empty_dir_returns_default(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        cat = categorizePrompt("any prompt at all", empty)
        assert cat == DEFAULT_CATEGORY

    def test_low_score_triggers_backoff(self, category_dir):
        # A totally novel prompt should still return something valid (not crash)
        cat = categorizePrompt("xyzzy quux blorple frobozz", category_dir)
        assert isinstance(cat, str)


# ---------------------------------------------------------------------------
# scoreChain / rankChains
# ---------------------------------------------------------------------------


class TestScoreChain:
    def test_relevant_prompt_scores_higher(self, category_dir):
        _, idf, _ = buildChainIndex(category_dir)
        chains = loadReasoningChains("math.md", category_dir)
        arithmetic = next(c for c in chains if c[0] == "Arithmetic")
        algebra = next(c for c in chains if c[0] == "Algebra")
        sArith = scoreChain("calculate multiply arithmetic", arithmetic, idf)
        sAlg = scoreChain("calculate multiply arithmetic", algebra, idf)
        assert sArith >= sAlg

    def test_tool_result_bonus_applied(self, category_dir):
        _, idf, _ = buildChainIndex(category_dir)
        chains = loadReasoningChains("math.md", category_dir)
        chain = chains[0]
        withoutBonus = scoreChain("test", chain, idf, has_tool_result=False)
        withBonus = scoreChain("test", chain, idf, has_tool_result=True)
        assert withBonus >= withoutBonus


class TestRankChains:
    def test_returns_at_most_max_paths(self, category_dir):
        _, idf, _ = buildChainIndex(category_dir)
        chains = loadReasoningChains("math.md", category_dir)
        ranked = rankChains("calculate solve equation", chains, idf)
        assert len(ranked) <= MAX_EVALUATED_PATHS

    def test_first_result_has_highest_score(self, category_dir):
        _, idf, _ = buildChainIndex(category_dir)
        chains = loadReasoningChains("math.md", category_dir)
        ranked = rankChains("calculate", chains, idf)
        scores = [s for _, s in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_greedy_fast_path_single_nonzero(self, category_dir):
        _, idf, _ = buildChainIndex(category_dir)
        chains = loadReasoningChains("math.md", category_dir)
        # Use a very specific term that only matches one chain
        ranked = rankChains("quadratic factoring polynomial", chains, idf)
        # Should not crash; result should be non-empty
        assert len(ranked) >= 1

    def test_empty_chains_returns_empty(self, category_dir):
        _, idf, _ = buildChainIndex(category_dir)
        assert rankChains("anything", [], idf) == []


# ---------------------------------------------------------------------------
# scoreResponse
# ---------------------------------------------------------------------------


class TestScoreResponse:
    def test_empty_knowledge_dir_returns_zero(self, tmp_path):
        empty = tmp_path / "knowledge"
        empty.mkdir()
        assert scoreResponse("anything at all", empty) == 0.0

    def test_blank_text_returns_zero(self, tmp_path):
        empty = tmp_path / "knowledge"
        empty.mkdir()
        assert scoreResponse("   ", empty) == 0.0

    def test_score_in_unit_range(self):
        from tinytot.retrieval import buildKnowledgeIndex

        buildKnowledgeIndex.cache_clear()
        score = scoreResponse("Paris is the capital of France")
        assert 0.0 <= score <= 1.0
        buildKnowledgeIndex.cache_clear()

    def test_relevant_scores_higher_than_nonsense(self):
        from tinytot.retrieval import buildKnowledgeIndex

        buildKnowledgeIndex.cache_clear()
        relevant = scoreResponse("Paris is the capital of France and its largest city")
        nonsense = scoreResponse("zorbax fribble quux blorple xyzzy")
        assert relevant > nonsense
        buildKnowledgeIndex.cache_clear()

    def test_result_is_float(self, tmp_path):
        empty = tmp_path / "knowledge"
        empty.mkdir()
        result = scoreResponse("test text", empty)
        assert isinstance(result, float)
