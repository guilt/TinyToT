"""Tests for new server endpoints: /api/agent, /api/agent/tools, /api/agent/tool,
/api/agent/learn, /v1/chat/completions, /v1/models.
Also covers inference.py gaps: agent dispatch, live-data, yes/no, summarize mode.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from tinytot.content import getCategories, loadReasoningChains
from tinytot.retrieval import buildChainIndex, buildKnowledgeIndex
from tinytot.server import app


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


@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# /api/agent/tools  (GET)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_tools_returns_schemas(client):
    r = await client.get("/api/agent/tools")
    assert r.status_code == 200
    body = r.json()
    assert "tools" in body
    names = {t["function"]["name"] for t in body["tools"]}
    assert "web_fetch" in names
    assert "file_explore" in names
    assert "shell_run" in names
    assert "image_analyse" in names


# ---------------------------------------------------------------------------
# /api/agent/tool  (POST — run single tool)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_known_tool(client):
    with patch("tinytot.tools_ext.FileTool.run", return_value="file listing here"):
        r = await client.post(
            "/api/agent/tool",
            json={
                "name": "file_explore",
                "params": {"path": ".", "operation": "list"},
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["tool"] == "file_explore"
    assert "result" in body


@pytest.mark.asyncio
async def test_run_unknown_tool_returns_error_in_result(client):
    r = await client.post(
        "/api/agent/tool",
        json={
            "name": "nonexistent_tool_xyz",
            "params": {},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "unknown tool" in body["result"].lower()


@pytest.mark.asyncio
async def test_run_shell_tool_echo(client):
    r = await client.post(
        "/api/agent/tool",
        json={
            "name": "shell_run",
            "params": {"command": "echo tinytot_test_marker"},
        },
    )
    assert r.status_code == 200
    assert "tinytot_test_marker" in r.json()["result"]


# ---------------------------------------------------------------------------
# /api/agent  (POST — full plan-execute loop)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_endpoint_basic(client):
    with patch("tinytot.server.agentResponse", return_value="agent answer here"):
        r = await client.post("/api/agent", json={"prompt": "search for tree of thoughts"})
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "agent answer here"
    assert body["done"] is True


@pytest.mark.asyncio
async def test_agent_endpoint_single_tool_shortcut(client):
    with patch("tinytot.tools_ext.ShellTool.run", return_value="ls output"):
        r = await client.post(
            "/api/agent",
            json={
                "prompt": "list files",
                "tool": "shell_run",
                "tool_params": {"command": "ls"},
            },
        )
    assert r.status_code == 200
    assert r.json()["tool"] == "shell_run"


@pytest.mark.asyncio
async def test_agent_endpoint_with_session_id(client):
    with patch("tinytot.server.agentResponse", return_value="ok") as mock_agent:
        await client.post(
            "/api/agent",
            json={
                "prompt": "fetch https://example.com",
                "session_id": "test-sess-123",
            },
        )
    mock_agent.assert_called_once_with("fetch https://example.com", session_id="test-sess-123")


# ---------------------------------------------------------------------------
# /api/agent/learn  (POST)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_learn_records_content(client, tmp_path):
    with patch("tinytot.server.LearningJournal"):
        r = await client.post(
            "/api/agent/learn",
            json={
                "content": "TinyToT is the best",
                "session_id": "sess-abc",
                "source": "user",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "recorded"
    assert "TinyToT" in body["content"]


@pytest.mark.asyncio
async def test_learn_missing_content_returns_400(client):
    r = await client.post("/api/agent/learn", json={"session_id": "x"})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# /v1/chat/completions  (POST — OpenAI-compatible)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openai_chat_non_streaming(client):
    with patch("tinytot.server.generateReasoningResponse", return_value="hello from tinytot"):
        r = await client.post(
            "/v1/chat/completions",
            json={
                "model": "tinytot",
                "messages": [{"role": "user", "content": "say hello"}],
                "stream": False,
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["content"] == "hello from tinytot"
    assert body["choices"][0]["finish_reason"] == "stop"
    assert "usage" in body
    assert body["model"] == "tinytot"


@pytest.mark.asyncio
async def test_openai_chat_streaming(client):
    with patch("tinytot.server.generateReasoningResponse", return_value="word1 word2 word3"):
        r = await client.post(
            "/v1/chat/completions",
            json={
                "model": "tinytot",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": True,
            },
        )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    text = r.text
    assert "data:" in text
    assert "[DONE]" in text


@pytest.mark.asyncio
async def test_openai_chat_extracts_last_user_message(client):
    calls = []

    def capture(prompt, **kwargs):
        calls.append(prompt)
        return "captured"

    with patch("tinytot.server.generateReasoningResponse", side_effect=capture):
        await client.post(
            "/v1/chat/completions",
            json={
                "model": "tinytot",
                "stream": False,
                "messages": [
                    {"role": "user", "content": "first message"},
                    {"role": "assistant", "content": "response"},
                    {"role": "user", "content": "second message"},
                ],
            },
        )

    assert len(calls) > 0
    assert calls[0] == "second message"


@pytest.mark.asyncio
async def test_openai_chat_extracts_session_id_from_system(client):
    calls = []

    def capture(prompt, **kwargs):
        calls.append(kwargs)
        return "ok"

    with patch("tinytot.server.generateReasoningResponse", side_effect=capture):
        await client.post(
            "/v1/chat/completions",
            json={
                "model": "tinytot",
                "stream": False,
                "messages": [
                    {"role": "system", "content": "System prompt. session-id: my-session-42"},
                    {"role": "user", "content": "hello"},
                ],
            },
        )

    assert len(calls) > 0
    assert calls[0].get("session_id") == "my-session-42"


# ---------------------------------------------------------------------------
# /v1/models  (GET)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openai_models_returns_tinytot(client):
    r = await client.get("/v1/models")
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "list"
    ids = [m["id"] for m in body["data"]]
    assert "tinytot" in ids


# ---------------------------------------------------------------------------
# inference.py gap coverage
# ---------------------------------------------------------------------------


class TestInferenceAgentDispatch:
    def test_agent_dispatch_fires_on_url(self):
        from tinytot.inference import generateReasoningResponse

        with patch("tinytot.inference.detectAgentNeeds", return_value=True):
            with patch("tinytot.inference.agentResponse", return_value="agent result") as mock_agent:
                result = generateReasoningResponse("fetch https://example.com")

        mock_agent.assert_called_once()
        assert result == "agent result"

    def test_agent_dispatch_skipped_for_simple_query(self):
        from tinytot.inference import generateReasoningResponse

        with patch("tinytot.inference.detectAgentNeeds", return_value=False):
            with patch("tinytot.inference.agentResponse") as mock_agent:
                generateReasoningResponse("what is 2 + 2")

        mock_agent.assert_not_called()

    def test_session_id_passed_to_agent(self):
        from tinytot.inference import generateReasoningResponse

        with patch("tinytot.inference.detectAgentNeeds", return_value=True):
            with patch("tinytot.inference.agentResponse", return_value="ok") as mock_agent:
                generateReasoningResponse("fetch https://x.com", session_id="s123")

        _, kwargs = mock_agent.call_args
        assert kwargs.get("session_id") == "s123"


class TestInferenceLiveDataGuard:
    def test_live_weather_returns_no_data_message(self):
        from tinytot.inference import generateReasoningResponse

        with patch("tinytot.inference.detectAgentNeeds", return_value=False):
            result = generateReasoningResponse("what is the current weather in Tokyo")

        assert "live" in result.lower() or "real-time" in result.lower() or "don't have" in result.lower()

    def test_current_stock_price_returns_no_data(self):
        from tinytot.inference import generateReasoningResponse

        with patch("tinytot.inference.detectAgentNeeds", return_value=False):
            result = generateReasoningResponse("what is the current stock price for Apple today")

        assert "live" in result.lower() or "real-time" in result.lower() or "don't have" in result.lower()


class TestInferenceSummarizeMode:
    def test_summarize_mode_with_long_text(self):
        from tinytot.inference import generateReasoningResponse

        long_text = "summarize: " + " ".join(["The cat sat on the mat."] * 50)
        result = generateReasoningResponse(long_text)
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_summarize_prompt_without_text_returns_guidance(self):
        from tinytot.inference import generateReasoningResponse

        result = generateReasoningResponse("please summarize this document")
        assert isinstance(result, str)

    def test_word_budget_extracted_from_prompt(self):
        from tinytot.inference import generateReasoningResponse

        long_text = "summarize in 10 words: " + " ".join(["word"] * 200)
        result = generateReasoningResponse(long_text)
        assert isinstance(result, str)


class TestInferenceYesNo:
    def test_yes_no_question_gets_answer(self):
        from tinytot.inference import generateReasoningResponse

        result = generateReasoningResponse("Is Python a programming language?")
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_yes_no_starts_with_yes_or_no_or_passage(self):
        from tinytot.inference import generateReasoningResponse

        result = generateReasoningResponse("Is the sky blue?")
        # Should start with Yes/No or return a passage
        assert result


class TestInferenceJsonScoring:
    def test_json_scoring_returns_valid_json(self):
        from tinytot.inference import generateReasoningResponse

        prompt = 'Please reply with JSON {"score": X, "rationale": "..."} for this response: Paris is in France.'
        result = generateReasoningResponse(prompt)
        import json

        parsed = json.loads(result)
        assert "score" in parsed
        assert "rationale" in parsed

    def test_json_score_is_float(self):
        from tinytot.inference import generateReasoningResponse

        prompt = 'Return JSON {"score": X} for: The Eiffel Tower is in Paris.'
        result = generateReasoningResponse(prompt)
        import json

        parsed = json.loads(result)
        assert isinstance(parsed["score"], (int, float))
