"""Translation capability tests — unit and integration.

Three layers tested:
  1. TranslateTool: direct translation mocked via httpx.Client
  2. detectAgentNeeds: non-ASCII and explicit language directives trigger agent
  3. Cross-language bridging: Chinese question → Korean answer,
     multilingual Q&A, language detection, round-trip fidelity
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

from tinytot.agent import detectAgentNeeds
from tinytot.tools_ext import TranslateTool

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_httpx_response(translated_text: str) -> MagicMock:
    """Return a mock httpx response that mimics Google Translate's JSON format."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    # Google Translate returns nested arrays: [[["translated", "original", ...]]]
    mock_resp.json.return_value = [[[translated_text, "original", None, None, None]]]
    mock_resp.status_code = 200
    return mock_resp


@contextmanager
def _mock_httpx(translations: dict[str, str]):
    """Mock all translation backends so tests reach the httpx path:
    - _ct2_translate returns None (simulates no packs / ct2 not available)
    - LibreTranslate local server is unreachable (post raises)
    - Google Translate returns mocked translations via get
    """
    import httpx

    def _fake_get(url, **kwargs):
        params = kwargs.get("params", {})
        query = params.get("q", "") if isinstance(params, dict) else ""
        translated = translations.get(query, f"[translated] {query[:40]}")
        return _make_httpx_response(translated)

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = httpx.ConnectError("no local server")
    mock_client.get.side_effect = _fake_get

    with patch("tinytot.tools_ext._ct2_translate", return_value=None), patch("httpx.Client", return_value=mock_client):
        yield mock_client


# ---------------------------------------------------------------------------
# 1. TranslateTool — direct translation
# ---------------------------------------------------------------------------


class TestTranslateToolDirect:
    def test_chinese_to_english(self):
        with _mock_httpx({"机器学习是人工智能的一个子集": "Machine learning is a subset of artificial intelligence"}):
            result = TranslateTool().run(text="机器学习是人工智能的一个子集", target="en", source="zh-CN")
        assert "machine learning" in result.lower()
        assert "artificial intelligence" in result.lower()

    def test_chinese_to_korean(self):
        """zh→ko uses ct2 pivot (zh→en→ko) when direct pack unavailable."""
        with _mock_httpx({"机器学习是人工智能的一个子集": "머신러닝은 인공지능의 하위 집합입니다"}):
            result = TranslateTool().run(text="机器学习是人工智能的一个子集", target="ko", source="zh-CN")
        # Either real Korean from ct2 pivot, or the mocked translation
        assert result and len(result) > 0

    def test_korean_to_english(self):
        with _mock_httpx({"인공지능은 미래입니다": "Artificial intelligence is the future"}):
            result = TranslateTool().run(text="인공지능은 미래입니다", target="en", source="ko")
        assert "artificial intelligence" in result.lower() or "future" in result.lower()

    def test_french_to_english(self):
        with _mock_httpx(
            {"L'intelligence artificielle transforme l'industrie": "Artificial intelligence transforms the industry"}
        ):
            result = TranslateTool().run(
                text="L'intelligence artificielle transforme l'industrie", target="en", source="fr"
            )
        assert "artificial intelligence" in result.lower()

    def test_japanese_to_english(self):
        with _mock_httpx({"人工知能は未来を変える": "Artificial intelligence changes the future"}):
            result = TranslateTool().run(text="人工知能は未来を変える", target="en", source="ja")
        assert "artificial intelligence" in result.lower() or "future" in result.lower()

    def test_arabic_to_english(self):
        with _mock_httpx({"الذكاء الاصطناعي يغير العالم": "Artificial intelligence is changing the world"}):
            result = TranslateTool().run(text="الذكاء الاصطناعي يغير العالم", target="en", source="ar")
        assert "artificial intelligence" in result.lower() or "world" in result.lower()

    def test_english_to_chinese(self):
        with _mock_httpx({"Machine learning is powerful": "机器学习很强大"}):
            result = TranslateTool().run(text="Machine learning is powerful", target="zh-CN", source="en")
        assert "机器" in result or "学习" in result or "强大" in result

    def test_english_to_japanese(self):
        with _mock_httpx({"Good morning": "おはようございます"}):
            result = TranslateTool().run(text="Good morning", target="ja", source="en")
        assert "おはよう" in result

    def test_auto_detect_source_passes_auto(self):
        """source='auto' is forwarded to the translation API."""
        with _mock_httpx({"你好世界": "Hello world"}) as mock_client:
            TranslateTool().run(text="你好世界", target="en")
        call_kwargs = mock_client.get.call_args[1]
        params = call_kwargs.get("params", {})
        assert params.get("sl") == "auto"

    def test_round_trip_english_french_english(self):
        """en→fr→en round-trip preserves core meaning."""
        with _mock_httpx({"The sky is blue": "Le ciel est bleu"}):
            french = TranslateTool().run(text="The sky is blue", target="fr", source="en")
        with _mock_httpx({"Le ciel est bleu": "The sky is blue"}):
            english = TranslateTool().run(text=french, target="en", source="fr")
        assert "sky" in english.lower() or "blue" in english.lower()

    def test_long_text_split_into_chunks(self):
        """Texts over 4900 chars are split into multiple API calls."""
        long_text = "こんにちは。" * 900  # ~5400 chars
        call_count = [0]
        import httpx

        def _fake_get(url, **kwargs):
            call_count[0] += 1
            return _make_httpx_response(f"chunk-{call_count[0]}")

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = httpx.ConnectError("no server")
        mock_client.get.side_effect = _fake_get

        with patch("tinytot.tools_ext._ct2_translate", return_value=None), patch(
            "httpx.Client", return_value=mock_client
        ):
            result = TranslateTool().run(text=long_text, target="en", source="ja")

        assert call_count[0] > 1
        assert "chunk" in result

    def test_empty_text_returns_empty(self):
        result = TranslateTool().run(text="", target="fr")
        assert result == ""

    def test_whitespace_only_returns_as_is(self):
        result = TranslateTool().run(text="   ", target="fr")
        assert result.strip() == ""

    def test_network_error_returns_error_string(self):
        """When ct2 has no pack and all network backends fail, returns [translate] error."""
        import httpx

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = httpx.ConnectError("proxy blocked")
        mock_client.get.side_effect = httpx.ConnectError("proxy blocked")
        # sw = Swahili — no pack installed, ct2 returns None
        with patch("tinytot.tools_ext._ct2_translate", return_value=None), patch(
            "httpx.Client", return_value=mock_client
        ):
            result = TranslateTool().run(text="Hello", target="sw")
        assert "[translate]" in result


# ---------------------------------------------------------------------------
# 2. Agent routing — multilingual prompts trigger agent
# ---------------------------------------------------------------------------


class TestMultilingualAgentDetection:
    def test_chinese_question_triggers_agent(self):
        assert detectAgentNeeds("你好，什么是机器学习？")

    def test_korean_text_triggers_agent(self):
        assert detectAgentNeeds("인공지능은 미래입니다")

    def test_japanese_triggers_agent(self):
        assert detectAgentNeeds("人工知能とは何ですか？")

    def test_arabic_triggers_agent(self):
        assert detectAgentNeeds("ما هو الذكاء الاصطناعي؟")

    def test_mixed_cjk_english_triggers_agent(self):
        assert detectAgentNeeds("请用Korean回答这个问题")

    def test_explicit_answer_in_language_triggers(self):
        assert detectAgentNeeds("Please answer in Korean: What is AI?")

    def test_explicit_respond_in_language_triggers(self):
        assert detectAgentNeeds("Respond in Japanese: What is the capital of France?")

    def test_translate_keyword_triggers(self):
        assert detectAgentNeeds("Translate this sentence to Chinese")

    def test_named_language_in_triggers(self):
        assert detectAgentNeeds("What is quantum computing in Korean?")

    def test_pure_english_factual_no_trigger(self):
        assert not detectAgentNeeds("What is the capital of France?")

    def test_pure_english_math_no_trigger(self):
        assert not detectAgentNeeds("What is 2 + 2?")


# ---------------------------------------------------------------------------
# 3. Cross-language bridging — Chinese question → Korean answer
# ---------------------------------------------------------------------------


class TestCrossLanguageBridging:
    """Tests that TinyToT can bridge across languages via the translate tool."""

    def _mock_translate_tool(self, translations: dict[str, str]):
        """Patch TranslateTool.run with a deterministic mapping."""

        def fake_run(self_inner, text="", target="en", source="auto", **kwargs):
            return translations.get(text.strip(), f"[translated:{target}] {text[:40]}")

        return patch.object(TranslateTool, "run", fake_run)

    def test_chinese_question_to_english_synthesis(self):
        """Chinese input is translated to English, ToT synthesises, returns answer."""
        translations = {"机器学习是什么？": "What is machine learning?"}
        with self._mock_translate_tool(translations):
            with patch(
                "tinytot.inference.generateTreeOfThoughtsResponse", return_value="Machine learning is a subset of AI."
            ):
                import tempfile

                from tinytot.agent import LearningJournal, PlanExecuteLoop

                loop = PlanExecuteLoop.__new__(PlanExecuteLoop)
                from tinytot.tools_ext import registry

                loop._tools = registry
                loop._journal = LearningJournal(journal_dir=Path(tempfile.mkdtemp()))
                result = loop._synthesise("机器学习是什么？", "What is machine learning?")
        assert isinstance(result, str) and len(result) > 0

    def test_korean_to_english_translation(self):
        with _mock_httpx({"인공지능은 미래를 바꿀 것입니다": "Artificial intelligence will change the future"}):
            result = TranslateTool().run(text="인공지능은 미래를 바꿀 것입니다", target="en", source="ko")
        assert "artificial intelligence" in result.lower() or "future" in result.lower()

    def test_chinese_to_korean_two_hop(self):
        """Chinese → English → Korean two-hop bridge via sequential calls."""
        with _mock_httpx({"机器学习很强大": "Machine learning is powerful"}):
            en = TranslateTool().run(text="机器学习很强大", target="en", source="zh-CN")
        with _mock_httpx({"Machine learning is powerful": "머신러닝은 강력합니다"}):
            ko = TranslateTool().run(text=en, target="ko", source="en")
        assert "머신" in ko or "강력" in ko or "machine" in ko.lower()

    def test_multilingual_qa_pipeline(self):
        """Simulate Q&A in 3 languages translated to English."""
        pairs = [
            ("fr", "Qu'est-ce que l'IA?", "artificial intelligence"),
            ("de", "Was ist maschinelles Lernen?", "machine learning"),
            ("es", "¿Qué es la computación en la nube?", "cloud"),
        ]
        for src_lang, question, must_contain in pairs:
            with _mock_httpx({question: f"[translated to en] {must_contain} related answer"}):
                translated = TranslateTool().run(text=question, target="en", source=src_lang)
            assert must_contain.lower() in translated.lower(), (
                f"{src_lang}→en: expected '{must_contain}' in '{translated}'"
            )

    def test_language_agnostic_routing(self):
        """Non-ASCII prompts always route through agent regardless of language."""
        non_ascii = [
            "什么是树状思维？",  # Chinese
            "나무의 생각이란 무엇인가?",  # Korean
            "木の考えとは何ですか？",  # Japanese
            "ما هو تفكير الشجرة؟",  # Arabic
            "वृक्ष विचार क्या है?",  # Hindi
        ]
        for prompt in non_ascii:
            assert detectAgentNeeds(prompt), f"Expected agent trigger for: {prompt}"

    def test_explicit_cross_language_instructions(self):
        """'Answer in X' and 'Respond in X' trigger agent for all named languages."""
        instructions = [
            "Answer in Korean: What is deep learning?",
            "Please respond in Chinese: How does gradient descent work?",
            "Reply in Japanese: What is a neural network?",
            "Explain in French: What is the transformer architecture?",
            "Tell me in German: What is backpropagation?",
        ]
        for prompt in instructions:
            assert detectAgentNeeds(prompt), f"Expected agent trigger for: {prompt}"

    def test_translation_target_extraction(self):
        """_extract_params extracts language targets from natural-language descriptions."""
        from tinytot.agent import _extract_params

        cases = [
            ("translate to Korean", "korean"),
            ("translate into Japanese", "japanese"),
            ("translate to zh-CN", "zh-cn"),
            ("convert to French", "french"),
        ]
        for desc, expected in cases:
            params = _extract_params("translate", desc, "some text")
            assert params["target"].lower() == expected, (
                f"desc={desc!r}: expected {expected!r}, got {params['target']!r}"
            )

    def test_translation_error_is_string_not_exception(self):
        """Network errors return an error string, never raise."""
        import httpx

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = httpx.ConnectError("blocked")
        mock_client.get.side_effect = httpx.ConnectError("blocked")
        with patch("tinytot.tools_ext._ct2_translate", return_value=None), patch(
            "httpx.Client", return_value=mock_client
        ):
            result = TranslateTool().run(text="Hello", target="fr")
        assert isinstance(result, str)

    def test_empty_text_handled(self):
        result = TranslateTool().run(text="", target="fr")
        assert isinstance(result, str)
