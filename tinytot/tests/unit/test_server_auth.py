"""Regression tests for GHSA-2f6r-9rrh-wvq9 (unauthenticated RCE).

Covers the loopback-by-default bind and bearer-token enforcement on the
tool-invoking routes.
"""

from __future__ import annotations

import logging
import sys
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from tinytot import server
from tinytot.server import app

TOKEN = "s3cret-test-token"


@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


def test_default_host_is_loopback():
    assert server.DEFAULT_HOST == "127.0.0.1"


def test_host_addr_env_default(monkeypatch):
    monkeypatch.delenv(server.HOST_ADDR_ENV, raising=False)
    assert server._configured_host() == "127.0.0.1"


def test_host_addr_env_override(monkeypatch):
    monkeypatch.setenv(server.HOST_ADDR_ENV, "0.0.0.0")
    assert server._configured_host() == "0.0.0.0"


def test_startup_guard_honours_host_addr_env(monkeypatch):
    monkeypatch.delenv(server.API_TOKEN_ENV, raising=False)
    monkeypatch.setenv(server.HOST_ADDR_ENV, "0.0.0.0")
    monkeypatch.setattr(sys, "argv", ["tinytot"])
    with pytest.raises(SystemExit) as exc:
        server.main()
    assert exc.value.code == 2


@pytest.mark.asyncio
async def test_tool_route_requires_token(client, monkeypatch):
    monkeypatch.setenv(server.API_TOKEN_ENV, TOKEN)
    r = await client.post(
        "/api/agent/tool",
        json={"name": "shell_run", "params": {"command": "echo hi"}},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_agent_route_rejects_wrong_token(client, monkeypatch):
    monkeypatch.setenv(server.API_TOKEN_ENV, TOKEN)
    r = await client.post(
        "/api/agent",
        json={"prompt": "x"},
        headers={"Authorization": "Bearer nope"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_tool_route_accepts_valid_token(client, monkeypatch):
    monkeypatch.setenv(server.API_TOKEN_ENV, TOKEN)
    r = await client.post(
        "/api/agent/tool",
        json={"name": "does_not_exist", "params": {}},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_learn_route_requires_token(client, monkeypatch):
    monkeypatch.setenv(server.API_TOKEN_ENV, TOKEN)
    r = await client.post("/api/agent/learn", json={"content": "x"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_chat_completions_requires_token(client, monkeypatch):
    monkeypatch.setenv(server.API_TOKEN_ENV, TOKEN)
    r = await client.post(
        "/v1/chat/completions",
        json={"model": "tinytot", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_loopback_allowed_without_token(client, monkeypatch):
    monkeypatch.delenv(server.API_TOKEN_ENV, raising=False)
    r = await client.post("/api/agent/tool", json={"name": "does_not_exist", "params": {}})
    assert r.status_code == 200


def test_startup_guard_refuses_public_bind_without_token(monkeypatch):
    monkeypatch.delenv(server.API_TOKEN_ENV, raising=False)
    monkeypatch.setattr(sys, "argv", ["tinytot", "--host", "0.0.0.0"])
    with pytest.raises(SystemExit) as exc:
        server.main()
    assert exc.value.code == 2


def test_startup_guard_allows_public_bind_with_token(monkeypatch):
    monkeypatch.setenv(server.API_TOKEN_ENV, TOKEN)
    monkeypatch.setattr(sys, "argv", ["tinytot", "--host", "0.0.0.0"])
    with patch.object(server.uvicorn, "run"):
        server.main()


@pytest.mark.asyncio
async def test_request_size_limit_returns_413(client, monkeypatch, caplog):
    monkeypatch.setenv(server.MAX_REQUEST_BYTES_ENV, "100")
    caplog.set_level(logging.WARNING, logger="tinytot.security")
    r = await client.post(
        "/api/agent/tool",
        json={"name": "does_not_exist", "params": {"text": "A" * 500}},
    )
    assert r.status_code == 413
    assert "request_too_large" in caplog.text


@pytest.mark.asyncio
async def test_request_size_limit_zero_disables(client, monkeypatch):
    monkeypatch.setenv(server.MAX_REQUEST_BYTES_ENV, "0")
    r = await client.post("/api/agent/tool", json={"name": "does_not_exist", "params": {}})
    assert r.status_code == 200


def test_invalid_request_size_limit_falls_back_to_default(monkeypatch):
    monkeypatch.setenv(server.MAX_REQUEST_BYTES_ENV, "not-a-number")
    assert server._max_request_bytes() == server.DEFAULT_MAX_REQUEST_BYTES


@pytest.mark.asyncio
async def test_default_limit_allows_long_contexts(client, monkeypatch):
    monkeypatch.delenv(server.MAX_REQUEST_BYTES_ENV, raising=False)
    r = await client.post(
        "/api/agent/tool",
        json={"name": "does_not_exist", "params": {"text": "A" * (1024 * 1024)}},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_auth_failure_is_logged_without_secrets(client, monkeypatch, caplog):
    monkeypatch.setenv(server.API_TOKEN_ENV, TOKEN)
    caplog.set_level(logging.WARNING, logger="tinytot.security")
    r = await client.post(
        "/api/agent",
        json={"prompt": "x"},
        headers={"Authorization": "Bearer wrong-secret"},
    )
    assert r.status_code == 401
    assert "auth_failed" in caplog.text
    assert "wrong-secret" not in caplog.text
    assert TOKEN not in caplog.text


@pytest.mark.asyncio
async def test_denied_tool_is_logged(client, monkeypatch, caplog):
    monkeypatch.delenv("TINYTOT_ENABLE_SHELL", raising=False)
    monkeypatch.delenv(server.API_TOKEN_ENV, raising=False)
    caplog.set_level(logging.WARNING, logger="tinytot.security")
    r = await client.post(
        "/api/agent/tool",
        json={"name": "shell_run", "params": {"command": "echo hi"}},
    )
    assert r.status_code == 200
    assert "tool_denied" in caplog.text
