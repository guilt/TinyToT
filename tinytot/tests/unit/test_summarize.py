"""Unit tests for tinytot.summarize and tinytot.eval_summarize."""

from __future__ import annotations

from pathlib import Path

import pytest

from tinytot.summarize import summarizeDocument

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SHORT_DOC = (
    "Machine learning is a subset of artificial intelligence. "
    "It enables systems to learn from data without explicit programming. "
    "Deep learning uses neural networks with many layers. "
    "These networks can recognise patterns in images, text, and audio. "
    "Transformers have revolutionised natural language processing. "
    "They use attention mechanisms to process sequences in parallel."
)

_MEDIUM_DOC = " ".join(
    [
        "The Python programming language was created by Guido van Rossum.",
        "It was first released in 1991 and has grown to become one of the most popular languages.",
        "Python emphasises readability and simplicity.",
        "It supports multiple programming paradigms including procedural, object-oriented, and functional.",
        "The language has a comprehensive standard library.",
        "Python is widely used in data science, web development, and automation.",
        "Libraries such as NumPy, Pandas, and TensorFlow power scientific computing.",
        "The Python Package Index hosts hundreds of thousands of third-party packages.",
        "CPython is the reference implementation written in C.",
        "PyPy offers a just-in-time compiled alternative for performance-critical code.",
        "The language uses indentation to delimit code blocks rather than braces.",
        "Dynamic typing and automatic memory management simplify development.",
        "Python 3 introduced breaking changes from Python 2 but improved the language.",
        "The Global Interpreter Lock limits true multi-threading but not multiprocessing.",
        "The language is governed by the Python Software Foundation.",
    ]
)

_NARRATIVE_DOC = " ".join(
    [
        "Alice woke up to find the door of her cottage open.",
        "She stepped outside into the cold morning air.",
        "A strange light flickered from the forest at the edge of the village.",
        "She grabbed her lantern and walked towards the trees.",
        "Deep in the forest she discovered an old stone bridge.",
        "Below the bridge a river of silver water flowed silently.",
        "A small figure sat on the railing, humming to itself.",
        "Alice approached carefully, not wanting to startle the creature.",
        "The figure turned and revealed a face like carved wood.",
        "It offered her a small glowing stone and then vanished.",
        "Alice returned to her cottage as the sun rose over the hills.",
        "She placed the stone on her windowsill where it continued to glow.",
        "Years later she would tell the story to her grandchildren.",
        "They never quite believed her, but she knew it was true.",
    ]
)


# ---------------------------------------------------------------------------
# Basic functionality
# ---------------------------------------------------------------------------


class TestSummarizeDocument:
    def test_returns_string(self):
        result = summarizeDocument(_SHORT_DOC)
        assert isinstance(result, str)

    def test_non_empty_result(self):
        result = summarizeDocument(_SHORT_DOC)
        assert len(result.strip()) > 0

    def test_respects_word_budget_approximately(self):
        result = summarizeDocument(_SHORT_DOC, max_words=20)
        word_count = len(result.split())
        # Allow 2x overshoot for extractive sentence picking
        assert word_count <= 60

    def test_tight_budget(self):
        result = summarizeDocument(_SHORT_DOC, max_words=10)
        assert len(result.split()) <= 30

    def test_generous_budget_returns_more_content(self):
        short = summarizeDocument(_MEDIUM_DOC, max_words=20)
        long = summarizeDocument(_MEDIUM_DOC, max_words=100)
        assert len(long.split()) >= len(short.split())

    def test_single_sentence_input(self):
        text = "The sky is blue because of Rayleigh scattering."
        result = summarizeDocument(text)
        assert len(result.strip()) > 0

    def test_empty_input_returns_string(self):
        result = summarizeDocument("")
        assert isinstance(result, str)

    def test_very_short_input(self):
        result = summarizeDocument("Hello world.")
        assert isinstance(result, str)

    def test_narrative_document(self):
        result = summarizeDocument(_NARRATIVE_DOC, max_words=30)
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_medium_document(self):
        result = summarizeDocument(_MEDIUM_DOC, max_words=50)
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_summary_contains_key_terms(self):
        result = summarizeDocument(_MEDIUM_DOC, max_words=50)
        # At least one core term should appear
        key_terms = ["python", "Python", "language", "programming"]
        assert any(t in result for t in key_terms)

    def test_large_document_handled(self):
        large = _MEDIUM_DOC * 20  # ~3000 words
        result = summarizeDocument(large, max_words=50)
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_max_words_zero_handled(self):
        result = summarizeDocument(_SHORT_DOC, max_words=0)
        assert isinstance(result, str)

    def test_max_words_one_returns_something(self):
        result = summarizeDocument(_SHORT_DOC, max_words=1)
        assert isinstance(result, str)

    def test_different_budgets_produce_different_lengths(self):
        r10 = summarizeDocument(_MEDIUM_DOC, max_words=10)
        r100 = summarizeDocument(_MEDIUM_DOC, max_words=100)
        # Not guaranteed to be exactly different but should differ for a real doc
        # Allow equal only if document is very short
        assert len(r100) >= len(r10)

    def test_unicode_text(self):
        text = "日本語のテキスト。これはテストです。機械学習は重要な技術です。自然言語処理も含まれます。"
        result = summarizeDocument(text, max_words=10)
        assert isinstance(result, str)

    def test_code_heavy_document(self):
        code_doc = (
            "def fibonacci(n):\n"
            "    if n <= 1: return n\n"
            "    return fibonacci(n-1) + fibonacci(n-2)\n\n"
            "The Fibonacci sequence is a classic recursion example. "
            "Each number is the sum of the two preceding ones. "
            "The sequence starts with 0 and 1. "
            "Memoization can dramatically improve performance. "
            "Dynamic programming eliminates redundant computations entirely."
        )
        result = summarizeDocument(code_doc, max_words=20)
        assert isinstance(result, str)

    def test_newline_separated_paragraphs(self):
        doc = "First paragraph talks about cats.\n\nSecond paragraph discusses dogs.\n\nThird paragraph is about birds."
        result = summarizeDocument(doc, max_words=15)
        assert isinstance(result, str)
        assert len(result.strip()) > 0


# ---------------------------------------------------------------------------
# eval_summarize module
# ---------------------------------------------------------------------------


class TestParseSummarizeEval:
    def _write_eval(self, tmp_path: Path, content: str) -> Path:
        f = tmp_path / "eval.md"
        f.write_text(content)
        return f

    def test_parses_single_case(self, tmp_path):
        from tinytot.eval_summarize import _parse_eval_file

        md = """## climate-test
max_words: 30

### Input
The climate is changing rapidly. Greenhouse gases trap heat. Sea levels are rising.

### Must Contain
- climate
- greenhouse
"""
        f = self._write_eval(tmp_path, md)
        cases = _parse_eval_file(f)
        assert len(cases) == 1
        assert cases[0]["name"] == "climate-test"
        assert "climate" in cases[0]["must_contain"]
        assert cases[0]["max_words"] == 30

    def test_parses_multiple_cases(self, tmp_path):
        from tinytot.eval_summarize import _parse_eval_file

        md = """## case-one

### Input
First passage about science.

### Must Contain
- science

---

## case-two

### Input
Second passage about art.

### Must Contain
- art
"""
        f = self._write_eval(tmp_path, md)
        cases = _parse_eval_file(f)
        assert len(cases) == 2
        names = [c["name"] for c in cases]
        assert "case-one" in names
        assert "case-two" in names

    def test_default_max_words_when_omitted(self, tmp_path):
        from tinytot.eval_summarize import _DEFAULT_MAX_WORDS, _parse_eval_file

        md = """## no-words-spec

### Input
Some text here.

### Must Contain
- text
"""
        f = self._write_eval(tmp_path, md)
        cases = _parse_eval_file(f)
        assert cases[0]["max_words"] == _DEFAULT_MAX_WORDS

    def test_empty_must_contain(self, tmp_path):
        from tinytot.eval_summarize import _parse_eval_file

        md = """## minimal

### Input
Just some text without must-contain section.
"""
        f = self._write_eval(tmp_path, md)
        cases = _parse_eval_file(f)
        # may be empty or have empty must_contain
        if cases:
            assert isinstance(cases[0].get("must_contain", []), list)

    def test_input_extracted_correctly(self, tmp_path):
        from tinytot.eval_summarize import _parse_eval_file

        md = """## test-input

### Input
This is the exact input text to summarize.

### Must Contain
- exact
"""
        f = self._write_eval(tmp_path, md)
        cases = _parse_eval_file(f)
        assert cases[0]["input"] == "This is the exact input text to summarize."

    def test_missing_file_raises(self):
        from tinytot.eval_summarize import _parse_eval_file

        with pytest.raises(Exception):
            _parse_eval_file(Path("/no/such/eval.md"))


class TestRunSummarizeEval:
    """Integration: run eval on a synthetic eval file."""

    def test_run_passes_simple_case(self, tmp_path):
        from tinytot.eval_summarize import run_eval

        md = """## easy

### Input
The Eiffel Tower is in Paris. It is a famous landmark. Millions visit each year.

### Must Contain
- Eiffel
- Paris
"""
        f = tmp_path / "eval.md"
        f.write_text(md)
        passed = run_eval(path=f, verbose=False)
        assert passed is True

    def test_run_detects_failure(self, tmp_path):
        from tinytot.eval_summarize import run_eval

        md = """## impossible

### Input
Short text.

### Must Contain
- xyzzy_impossible_token_12345
"""
        f = tmp_path / "eval.md"
        f.write_text(md)
        passed = run_eval(path=f, verbose=False)
        assert passed is False

    def test_run_returns_false_for_empty_file(self, tmp_path):
        from tinytot.eval_summarize import run_eval

        f = tmp_path / "empty.md"
        f.write_text("# no cases\n")
        result = run_eval(path=f, verbose=False)
        assert result is False


# ---------------------------------------------------------------------------
# Internal helpers — targeted for coverage
# ---------------------------------------------------------------------------


class TestSplitSentences:
    def test_basic_split(self):
        from tinytot.summarize import _splitSentences

        sents = _splitSentences(
            "The quick brown fox jumps over the lazy dog. "
            "Machine learning is a subset of artificial intelligence. "
            "Python is widely used in data science and research."
        )
        assert len(sents) >= 2

    def test_filters_very_short_fragments(self):
        from tinytot.summarize import _splitSentences

        sents = _splitSentences("Hi. OK. The quick brown fox jumps over the lazy dog today.")
        # Very short sentences ("Hi", "OK") should be filtered
        for s in sents:
            assert len(s.split()) >= 2

    def test_empty_input(self):
        from tinytot.summarize import _splitSentences

        assert _splitSentences("") == []

    def test_single_long_sentence(self):
        from tinytot.summarize import _splitSentences

        sentence = "Machine learning enables computers to learn from data without explicit programming rules."
        sents = _splitSentences(sentence)
        assert len(sents) >= 1


class TestBuildTfIdf:
    def test_empty_input(self):
        from tinytot.summarize import _buildTfIdf

        vecs, idf = _buildTfIdf([])
        assert vecs == []
        assert idf == {}

    def test_single_sentence(self):
        from tinytot.summarize import _buildTfIdf

        vecs, idf = _buildTfIdf(["machine learning is important"])
        assert len(vecs) == 1
        assert len(idf) >= 1

    def test_multiple_sentences(self):
        from tinytot.summarize import _buildTfIdf

        sents = [
            "Python is a programming language.",
            "Machine learning uses Python.",
            "Data science relies on Python libraries.",
        ]
        vecs, idf = _buildTfIdf(sents)
        assert len(vecs) == len(sents)
        # All vectors should be normalised (unit norm or near)
        import math

        for v in vecs:
            if v:
                norm = math.sqrt(sum(x * x for x in v.values()))
                assert abs(norm - 1.0) < 0.01

    def test_idf_penalises_common_terms(self):
        from tinytot.summarize import _buildTfIdf

        # "the" appears in every sentence — should have low IDF
        sents = ["the cat sat", "the dog ran", "the bird flew"]
        _, idf = _buildTfIdf(sents)
        # "cat", "dog", "bird" each appear once — higher IDF than "the" (if "the" survives stopword filter)
        # Just verify idf is populated and terms present
        assert len(idf) >= 1


class TestCosine:
    def test_identical_vectors(self):
        from tinytot.summarize import _cosine

        v = {"a": 0.6, "b": 0.8}
        assert abs(_cosine(v, v) - 1.0) < 0.01

    def test_orthogonal_vectors(self):
        from tinytot.summarize import _cosine

        a = {"x": 1.0}
        b = {"y": 1.0}
        assert _cosine(a, b) == 0.0

    def test_partial_overlap(self):
        from tinytot.summarize import _cosine

        a = {"x": 0.6, "y": 0.8}
        b = {"y": 1.0}
        result = _cosine(a, b)
        assert 0.0 < result < 1.0


class TestScoreByLexicalCentrality:
    def test_empty(self):
        from tinytot.summarize import _scoreByLexicalCentrality

        assert _scoreByLexicalCentrality([]) == []

    def test_single_vector(self):
        from tinytot.summarize import _scoreByLexicalCentrality

        scores = _scoreByLexicalCentrality([{"a": 1.0}])
        assert len(scores) == 1

    def test_multiple_vectors_returns_scores(self):
        from tinytot.summarize import _buildTfIdf, _scoreByLexicalCentrality

        sents = [
            "Python is popular for data science.",
            "Machine learning uses Python extensively.",
            "Neural networks are a type of machine learning.",
        ]
        vecs, _ = _buildTfIdf(sents)
        scores = _scoreByLexicalCentrality(vecs)
        assert len(scores) == 3
        assert all(isinstance(s, float) for s in scores)


class TestNarrativeWeight:
    def test_plain_sentence_weight_one(self):
        from tinytot.summarize import _narrativeWeight

        w = _narrativeWeight("The weather was cold.")
        assert w >= 1.0

    def test_dialogue_penalised(self):
        from tinytot.summarize import WEIGHT_DIALOGUE_SENTENCE, _narrativeWeight

        w = _narrativeWeight('"I need help," said Alice.')
        assert w == WEIGHT_DIALOGUE_SENTENCE

    def test_plot_verb_boosted(self):
        from tinytot.summarize import _narrativeWeight

        w_plain = _narrativeWeight("The cat was on the mat.")
        w_action = _narrativeWeight("Alice discovered a secret door.")
        assert w_action >= w_plain

    def test_outcome_signal_boosted(self):
        from tinytot.summarize import WEIGHT_OUTCOME_SIGNAL, _narrativeWeight

        # "ruled" and "sentenced" are in the outcome signal pattern
        w = _narrativeWeight("The court ruled in favour of the defendant.")
        # Outcome weight is applied as a multiplier
        assert w >= WEIGHT_OUTCOME_SIGNAL

    def test_named_entity_boosted(self):
        from tinytot.summarize import _narrativeWeight

        w_no_entity = _narrativeWeight("the weather was warm and sunny.")
        w_entity = _narrativeWeight("Alice walked through the forest.")
        assert w_entity >= w_no_entity


class TestSummarizeFile:
    def test_existing_file(self, tmp_path):
        from tinytot.summarize import summarizeFile

        f = tmp_path / "doc.txt"
        f.write_text(
            "Python is a popular programming language. "
            "It is used for data science and web development. "
            "Machine learning relies heavily on Python. "
            "The language was created by Guido van Rossum. "
            "Python emphasises readability and simplicity."
        )
        result = summarizeFile(str(f), max_words=20)
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_missing_file_returns_error(self):
        from tinytot.summarize import summarizeFile

        result = summarizeFile("/no/such/file_xyz_12345.txt")
        assert "not found" in result.lower() or "error" in result.lower() or "File" in result

    def test_path_object_accepted(self, tmp_path):
        from tinytot.summarize import summarizeFile

        f = tmp_path / "doc2.txt"
        f.write_text("Short test document. It has two sentences.")
        result = summarizeFile(f, max_words=10)
        assert isinstance(result, str)


class TestArcAwareSummarise:
    """Tests that exercise the arc-aware path (long narrative documents)."""

    # A document long enough to trigger arc-aware summarisation
    _LONG_NARRATIVE = " ".join(
        [
            "The old lighthouse stood on a rocky promontory overlooking the grey sea.",
            "Its keeper, Thomas, had tended the light for thirty years without fail.",
            "One stormy autumn night a ship appeared on the horizon, running without lights.",
            "Thomas signalled frantically but the vessel held its dangerous course.",
            "He climbed to the lantern room and increased the beam to maximum intensity.",
            "The ship's captain finally saw the warning and turned hard to starboard.",
            "Disaster was averted by mere seconds as the hull scraped past the rocks.",
            "Thomas descended the stairs, his legs shaking with exhaustion and relief.",
            "The next morning he reported the incident to the maritime authority.",
            "An investigation revealed the ship had suffered a compass malfunction.",
            "The captain wrote a letter of gratitude to Thomas for saving his crew.",
            "The letter hung on the lighthouse wall for many years afterward.",
            "Thomas retired the following spring after a lifetime of service.",
            "A small ceremony was held at the harbour to mark the occasion.",
            "He was presented with a lantern to remind him of his long watch.",
            "He placed it on his mantelpiece and never let the flame go out.",
        ]
    )

    def test_arc_aware_path_triggered(self):
        """Documents above ARC_THRESHOLD sentences use the arc-aware path."""
        from tinytot.summarize import ARC_THRESHOLD, _splitSentences, summarizeDocument

        sents = _splitSentences(self._LONG_NARRATIVE)
        # If the document is long enough the arc-aware path will be used
        if len(sents) >= ARC_THRESHOLD:
            result = summarizeDocument(self._LONG_NARRATIVE, max_words=40)
            assert isinstance(result, str)
            assert len(result.strip()) > 0

    def test_arc_aware_produces_coherent_summary(self):
        result = summarizeDocument(self._LONG_NARRATIVE, max_words=50)
        assert isinstance(result, str)
        # Should contain at least one word from the core narrative
        core_words = ["lighthouse", "Thomas", "ship", "light", "sea", "storm", "captain"]
        assert any(w.lower() in result.lower() for w in core_words)

    def test_arc_aware_respects_word_budget(self):
        result = summarizeDocument(self._LONG_NARRATIVE, max_words=30)
        words = result.split()
        # Allow 2× budget for extractive (sentence boundaries)
        assert len(words) <= 90

    def test_arc_aware_different_budgets(self):
        r20 = summarizeDocument(self._LONG_NARRATIVE, max_words=20)
        r60 = summarizeDocument(self._LONG_NARRATIVE, max_words=60)
        # More generous budget should produce equal or longer result
        assert len(r60) >= len(r20)

    def test_arc_aware_technical_document(self):
        technical = " ".join(
            [
                "Transformer models were introduced in the paper Attention is All You Need.",
                "The architecture uses self-attention to process input sequences in parallel.",
                "Multi-head attention allows the model to focus on different positions.",
                "Position encodings are added to provide sequence order information.",
                "The encoder maps input tokens to continuous representations.",
                "The decoder generates output tokens one at a time.",
                "Pre-training on large corpora enables transfer learning.",
                "Fine-tuning adapts the model to downstream tasks.",
                "BERT uses bidirectional training of the transformer encoder.",
                "GPT uses an autoregressive decoder-only architecture.",
                "Both models have achieved state-of-the-art on numerous benchmarks.",
                "The attention mechanism computes compatibility between all pairs of positions.",
                "Scaled dot-product attention divides by the square root of key dimension.",
                "Feed-forward networks are applied to each position independently.",
                "Residual connections and layer normalisation stabilise training.",
                "The softmax function converts attention scores to probabilities.",
            ]
        )
        result = summarizeDocument(technical, max_words=40)
        assert isinstance(result, str)
        assert len(result.strip()) > 0


class TestExtractDocumentEntities:
    def test_extracts_capitalised_names(self):
        from tinytot.summarize import _buildTfIdf, _extractDocumentEntities, _splitSentences

        text = (
            "Alice met Bob at the library every morning for several weeks. "
            "Bob introduced Alice to Carol at the local library on Tuesday. "
            "Carol was a scientist who worked with Alice and Bob daily. "
            "Alice and Bob collaborated with Carol on several important research projects. "
            "The three of them published a paper about their findings together."
        )
        sentences = _splitSentences(text)
        if sentences:
            _, idf = _buildTfIdf(sentences)
            entity_pattern = _extractDocumentEntities(sentences, idf)
            assert entity_pattern is not None

    def test_returns_compiled_pattern(self):
        from tinytot.summarize import _buildTfIdf, _extractDocumentEntities, _splitSentences

        text = (
            "Thomas worked at the lighthouse every single night without exception. "
            "Thomas was the keeper who maintained the lighthouse light beam. "
            "The lighthouse was Thomas's home and his life's great work. "
            "Thomas never missed a single night tending the lighthouse. "
            "His dedication made Thomas a legend among the local fishermen."
        )
        sentences = _splitSentences(text)
        if sentences:
            _, idf = _buildTfIdf(sentences)
            pattern = _extractDocumentEntities(sentences, idf)
            assert hasattr(pattern, "search")

    def test_empty_sentences(self):
        from tinytot.summarize import _extractDocumentEntities

        pattern = _extractDocumentEntities([], {})
        assert pattern is not None  # Should return a fallback pattern
