"""
Integration tests for tinytot.server — FastAPI endpoints via httpx.AsyncClient.

These tests spin up the FastAPI app in-process (no real uvicorn) using
httpx.AsyncClient with ASGITransport. They test wire format and routing;
for logic coverage see the unit tests.
"""

import json

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from tinytot.content import getCategories, loadReasoningChains
from tinytot.retrieval import buildChainIndex
from tinytot.server import app


@pytest.fixture(autouse=True)
def clear_caches():
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()
    buildChainIndex.cache_clear()
    yield
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()
    buildChainIndex.cache_clear()


@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# /api/tags
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tags_returns_tinytot_model(client):
    r = await client.get("/api/tags")
    assert r.status_code == 200
    body = r.json()
    assert any(m["name"] == "tinytot" for m in body["models"])


# ---------------------------------------------------------------------------
# /api/show
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_show_returns_model_info(client):
    r = await client.post("/api/show", json={"name": "tinytot"})
    assert r.status_code == 200
    body = r.json()
    assert "model_info" in body
    assert body["model_info"]["general.architecture"] == "tinytot"


# ---------------------------------------------------------------------------
# /api/pull
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pull_returns_success(client):
    r = await client.post("/api/pull", json={"name": "tinytot"})
    assert r.status_code == 200
    assert r.json()["status"] == "success"


# ---------------------------------------------------------------------------
# /api/generate — non-streaming
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_non_stream_returns_response(client):
    r = await client.post(
        "/api/generate",
        json={
            "model": "tinytot",
            "prompt": "calculate the area of a circle with radius 5",
            "stream": False,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["done"] is True
    assert isinstance(body["response"], str)
    assert len(body["response"]) > 0


# ---------------------------------------------------------------------------
# /api/generate — streaming
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_stream_sends_ndjson(client):
    r = await client.post(
        "/api/generate",
        json={
            "model": "tinytot",
            "prompt": "solve the equation",
            "stream": True,
        },
    )
    assert r.status_code == 200
    lines = [line for line in r.text.strip().splitlines() if line]
    assert len(lines) > 1
    last = json.loads(lines[-1])
    assert last["done"] is True


# ---------------------------------------------------------------------------
# /api/chat — no tools, non-streaming
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_no_tools_non_stream(client):
    r = await client.post(
        "/api/chat",
        json={
            "model": "tinytot",
            "messages": [{"role": "user", "content": "calculate 2 plus 2"}],
            "stream": False,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["done"] is True
    assert body["message"]["role"] == "assistant"
    assert isinstance(body["message"]["content"], str)


# ---------------------------------------------------------------------------
# /api/chat — with tool list, matching prompt, non-streaming
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_with_tools_returns_tool_call(client):
    r = await client.post(
        "/api/chat",
        json={
            "model": "tinytot",
            "messages": [{"role": "user", "content": "search for latest AI news"}],
            "stream": False,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "ddg__search",
                        "description": "DuckDuckGo search",
                        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                    },
                }
            ],
        },
    )
    assert r.status_code == 200
    body = r.json()
    msg = body["message"]
    assert "tool_calls" in msg
    assert len(msg["tool_calls"]) == 1
    assert "ddg" in msg["tool_calls"][0]["function"]["name"]


# ---------------------------------------------------------------------------
# /api/chat — with tool results already present (second turn)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_with_tool_results_returns_content(client):
    r = await client.post(
        "/api/chat",
        json={
            "model": "tinytot",
            "messages": [
                {"role": "user", "content": "search for AI"},
                {"role": "tool", "content": "Here are the AI search results."},
            ],
            "stream": False,
            "tools": [{"type": "function", "function": {"name": "ddg__search", "description": "search"}}],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "tool_calls" not in body["message"]
    content = body["message"]["content"]
    assert isinstance(content, str) and len(content) > 0
    # Response must be non-empty and must not echo "None"
    assert content.strip().lower() != "none"


@pytest.mark.asyncio
async def test_chat_with_none_tool_result_fallback(client):
    """When tool returns None/empty, TinyToT falls back to reasoning from the original question."""
    r = await client.post(
        "/api/chat",
        json={
            "model": "tinytot",
            "messages": [
                {"role": "user", "content": "search for AI news"},
                {"role": "tool", "content": "None"},
            ],
            "stream": False,
            "tools": [{"type": "function", "function": {"name": "ddg__search", "description": "search"}}],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "tool_calls" not in body["message"]
    assert isinstance(body["message"]["content"], str)
    assert body["message"]["content"].strip().lower() != "none"


@pytest.mark.asyncio
async def test_chat_with_tool_results_streaming(client):
    """Tool-result synthesis also works in streaming mode."""
    r = await client.post(
        "/api/chat",
        json={
            "model": "tinytot",
            "messages": [
                {"role": "user", "content": "search for AI"},
                {"role": "tool", "content": "Here are the AI search results."},
            ],
            "stream": True,
            "tools": [{"type": "function", "function": {"name": "ddg__search", "description": "search"}}],
        },
    )
    assert r.status_code == 200
    lines = [line for line in r.text.strip().splitlines() if line]
    assert len(lines) > 1
    last = json.loads(lines[-1])
    assert last["done"] is True


# ---------------------------------------------------------------------------
# /api/chat — streaming with no tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_stream_sends_ndjson(client):
    r = await client.post(
        "/api/chat",
        json={
            "model": "tinytot",
            "messages": [{"role": "user", "content": "solve algebra equation"}],
            "stream": True,
        },
    )
    assert r.status_code == 200
    lines = [line for line in r.text.strip().splitlines() if line]
    assert len(lines) > 1
    last = json.loads(lines[-1])
    assert last["done"] is True
