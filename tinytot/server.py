#!/usr/bin/env python3
"""
tinytot.server — FastAPI application and Ollama-compatible API endpoints.

Depends on tinytot.inference and tinytot.tools. All business logic lives
in the other modules; this file is purely routing and wire format.
"""

from __future__ import annotations

# Inject the secrets shim before any other import (secrets module compat).
from tinytot._secrets_shim import ensure_secrets  # isort: skip

ensure_secrets()

import json
import logging
import os
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__
from .agent import LearningJournal, agentResponse
from .inference import RESPONSE_TOOL_REASONING, generateReasoningResponse
from .summarize import summarizeDocument
from .tools import detectToolUsage, matchToolFromAvailable
from .tools_ext import registry as tool_registry

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_HOST: str = "0.0.0.0"
DEFAULT_PORT: int = int(os.getenv("PORT", "11434"))
STREAM_MEDIA_TYPE: str = "application/x-ndjson"
TOOL_CALL_ID_MODULO: int = 10000

app = FastAPI(title="TinyToT Server", description="Tree of Thoughts Inference Engine")

# Mount web UI
_web_dir = Path(__file__).parent / "_web" / "static"
if _web_dir.exists():
    app.mount("/web", StaticFiles(directory=str(_web_dir), html=True), name="web")


@app.get("/")
async def index():
    index_file = _web_dir / "index.html"
    if index_file.exists():
        html = index_file.read_text(encoding="utf-8")
        html = html.replace("{{VERSION}}", __version__)
        return HTMLResponse(html)
    return {"status": "TinyToT is running", "version": __version__, "docs": "/docs"}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: Optional[bool] = True
    options: Optional[Dict] = None
    think: Optional[bool] = None


class SummarizeRequest(BaseModel):
    document: str
    max_words: int = 50
    model: Optional[str] = "tinytot"


class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    stream: Optional[bool] = True
    options: Optional[Dict] = None
    tools: Optional[List[Dict]] = None
    think: Optional[bool] = None  # Ollama thinking-model flag (accepted; TinyToT always thinks)


class AgentRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = ""
    tool: Optional[str] = None  # run a specific tool directly
    tool_params: Optional[Dict] = None


class ToolRunRequest(BaseModel):
    name: str
    params: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Streaming helpers
# ---------------------------------------------------------------------------


async def _wordStream(text: str, model: str, chat: bool, thinking: str = ""):
    for word in text.split():
        if chat:
            chunk = {"model": model, "message": {"role": "assistant", "content": f"{word} "}, "done": False}
        else:
            chunk = {"response": f"{word} ", "done": False}
        yield json.dumps(chunk) + "\n"
    if chat:
        final_msg: dict = {"role": "assistant", "content": ""}
        if thinking:
            final_msg["thinking"] = thinking
        yield json.dumps({"model": model, "message": final_msg, "done": True}) + "\n"
    else:
        yield json.dumps({"response": "", "done": True}) + "\n"


def _split_thinking(text: str) -> tuple[str, str]:
    """Split a response into (thinking, content).

    If *text* starts with a ``<think>`` block, returns the block's inner text
    as *thinking* and everything after ``</think>`` as *content*.
    Otherwise returns ("", text).
    """
    import re

    m = re.match(r"<think>(.*?)</think>\s*(.*)", text, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", text


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    try:
        text = generateReasoningResponse(request.prompt)
        # /api/generate uses a flat "response" field — strip any <think> block so
        # only the clean answer is returned (thinking not defined in this protocol).
        _, response_text = _split_thinking(text)
        if request.stream:
            return StreamingResponse(
                _wordStream(response_text, request.model, chat=False), media_type=STREAM_MEDIA_TYPE
            )
        return {"model": request.model, "response": response_text, "done": True}
    except Exception as e:
        logger.error("Generate error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        userMessage = ""
        hasToolResults = False

        for msg in request.messages:
            if msg.get("role") == "user":
                userMessage = msg.get("content", "")
            if msg.get("role") == "tool" or "tool_calls" in msg:
                hasToolResults = True

        if request.tools and not hasToolResults:
            toolName, toolParams = detectToolUsage(userMessage)
            if toolName:
                matched = matchToolFromAvailable(toolName, request.tools)
                if matched:
                    reasoningText = RESPONSE_TOOL_REASONING.format(prompt=userMessage)
                    toolCall = {
                        "id": f"call_{hash(userMessage) % TOOL_CALL_ID_MODULO}",
                        "type": "function",
                        "function": {"name": matched["name"], "arguments": toolParams},
                    }

                    if request.stream:

                        async def _toolStream():
                            async for chunk in _wordStream(reasoningText, request.model, chat=True):
                                yield chunk
                            yield (
                                json.dumps(
                                    {
                                        "model": request.model,
                                        "message": {"role": "assistant", "content": "", "tool_calls": [toolCall]},
                                        "done": True,
                                    }
                                )
                                + "\n"
                            )

                        return StreamingResponse(_toolStream(), media_type=STREAM_MEDIA_TYPE)

                    return {
                        "model": request.model,
                        "message": {"role": "assistant", "content": reasoningText, "tool_calls": [toolCall]},
                        "done": True,
                    }

        if hasToolResults:
            toolResultContent = next((m.get("content", "") for m in request.messages if m.get("role") == "tool"), "")
            if not toolResultContent or toolResultContent.strip().lower() in ("none", "null", "", "error"):
                raw = generateReasoningResponse(userMessage, history=request.messages)
                thinking, content = _split_thinking(raw)
            else:
                synthesis_prompt = (
                    f"Based on this information: {toolResultContent}\n\nAnswer the question: {userMessage}"
                )
                from .inference import generateTreeOfThoughtsResponse

                trace = generateTreeOfThoughtsResponse(synthesis_prompt, direct_response=False)
                thinking, _ = _split_thinking(trace)
                if not thinking:
                    thinking = trace
                content = toolResultContent
            msg: dict = {"role": "assistant", "content": content}
            if thinking:
                msg["thinking"] = thinking
            if request.stream:
                return StreamingResponse(
                    _wordStream(content, request.model, chat=True, thinking=thinking),
                    media_type=STREAM_MEDIA_TYPE,
                )
            return {"model": request.model, "message": msg, "done": True}

        # Filter history to user/assistant turns only — system and tool messages
        # confuse buildContextPrompt which expects alternating user/assistant pairs.
        convoHistory = [m for m in request.messages if m.get("role") in ("user", "assistant")]
        text = generateReasoningResponse(userMessage, history=convoHistory)
        thinking, content = _split_thinking(text)
        msg = {"role": "assistant", "content": content}
        if thinking:
            msg["thinking"] = thinking
        if request.stream:
            return StreamingResponse(
                _wordStream(content, request.model, chat=True, thinking=thinking),
                media_type=STREAM_MEDIA_TYPE,
            )
        return {"model": request.model, "message": msg, "done": True}

    except Exception as e:
        logger.error("Chat error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/tags")
async def tags():
    return {
        "models": [
            {
                "name": "tinytot",
                "modifiedAt": "2024-01-20T00:00:00Z",
                "size": 0,
                "digest": "tinytot-digest",
                "details": {
                    "format": "gguf",
                    "family": "tinytot",
                    "families": ["tinytot"],
                    "parameterSize": "1B",
                    "quantizationLevel": "F32",
                },
                "capabilities": ["completion", "tools", "thinking"],
            }
        ]
    }


@app.post("/api/show")
async def show(request: dict):
    return {
        "license": "MIT",
        "modelfile": "# TinyToT Model\nFROM scratch\nPARAMETER temperature 0.7",
        "parameters": "temperature 0.7",
        "template": "{{ .Prompt }}",
        "details": {
            "format": "gguf",
            "family": "tinytot",
            "families": ["tinytot"],
            "parameterSize": "1B",
            "quantizationLevel": "F32",
        },
        "model_info": {
            "general.architecture": "tinytot",
            "general.file_type": 0,
            "general.parameter_count": 1_000_000_000,
            "general.quantization_version": 2,
            "tinytot.context_length": 65536,
            "tinytot.embedding_length": 4096,
            "tinytot.feed_forward_length": 14336,
            "tinytot.attention.head_count": 32,
            "tinytot.attention.head_count_kv": 8,
            "tinytot.attention.layer_count": 32,
            "tinytot.rope.freq_base": 500000.0,
        },
    }


@app.post("/api/pull")
async def pull(request: dict):
    return {"status": "success"}


@app.post("/api/summarize")
async def summarize(request: SummarizeRequest):
    """Extractive summarisation endpoint.

    Accepts a document of any length and returns an extractive summary.
    Works on novels, codebases, reports — no GPU, no neural weights.

    Example::

        curl http://localhost:11434/api/summarize \\
          -H "Content-Type: application/json" \\
          -d '{"document": "<full text of LoTR>", "max_words": 50}'
    """
    try:
        max_words = max(10, min(request.max_words, 2000))
        summary = summarizeDocument(request.document, max_words=max_words)
        return {
            "model": request.model,
            "summary": summary,
            "word_count": len(summary.split()),
            "max_words": max_words,
            "done": True,
        }
    except Exception as e:
        logger.error("Summarize error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Agent endpoint
# ---------------------------------------------------------------------------


@app.post("/api/agent")
async def agent(request: AgentRequest):
    """Agentic plan-execute endpoint.

    Runs the full PlanExecuteLoop: plan steps via ToT, execute via tools,
    synthesise a final answer grounded in the gathered context.

    Optionally run a single tool directly by setting ``tool`` and ``tool_params``.

    Example::

        curl http://localhost:11434/api/agent \\
          -H "Content-Type: application/json" \\
          -d '{"prompt": "Search for the latest paper on Tree of Thoughts and summarize it"}'
    """
    try:
        if request.tool:
            params = request.tool_params or {}
            result = tool_registry.run(request.tool, **params)
            return {"result": result, "tool": request.tool, "done": True}

        result = agentResponse(request.prompt, session_id=request.session_id or "")
        return {"result": result, "session_id": request.session_id, "done": True}
    except Exception as e:
        logger.error("Agent error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/agent/tools")
async def list_tools():
    """List all available agent tools and their schemas."""
    return {"tools": tool_registry.schemas()}


@app.post("/api/agent/tool")
async def run_tool(request: ToolRunRequest):
    """Run a single tool by name with explicit parameters.

    Example::

        curl http://localhost:11434/api/agent/tool \\
          -H "Content-Type: application/json" \\
          -d '{"name": "web_search", "params": {"query": "Tree of Thoughts paper"}}'
    """
    try:
        result = tool_registry.run(request.name, **request.params)
        return {"result": result, "tool": request.name, "done": True}
    except Exception as e:
        logger.error("Tool error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/agent/learn")
async def learn(body: Dict[str, Any]):
    """Record a learning to the journal.

    Example::

        curl http://localhost:11434/api/agent/learn \\
          -H "Content-Type: application/json" \\
          -d '{"content": "User prefers concise summaries", "session_id": "abc123"}'
    """
    content = body.get("content", "")
    session_id = body.get("session_id", "")
    source = body.get("source", "user")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    journal = LearningJournal()
    journal.record(content, source=source, session_id=session_id)
    return {"status": "recorded", "content": content[:80]}


# ---------------------------------------------------------------------------
# OpenAI-compatible endpoint (for Hermes and other OpenAI clients)
# ---------------------------------------------------------------------------


@app.post("/v1/chat/completions")
async def openai_chat(request: ChatRequest):
    """OpenAI-compatible chat completions endpoint.

    Allows Hermes and any OpenAI-compatible client to use TinyToT as its
    LLM backend.  Pass model='tinytot' (or any string).

    Streaming is supported via Server-Sent Events (text/event-stream).

    Example (Hermes config.yaml)::

        model: tinytot
        base_url: http://localhost:11434/v1
    """
    try:
        userMessage = ""
        for msg in reversed(request.messages):
            if msg.get("role") == "user":
                userMessage = msg.get("content", "")
                break
        if not userMessage:
            userMessage = request.messages[-1].get("content", "") if request.messages else ""

        # Extract session_id from system message metadata if present
        session_id = ""
        for msg in request.messages:
            if msg.get("role") == "system":
                m = re.search(r"session[_-]id:\s*(\S+)", msg.get("content", ""), re.IGNORECASE)
                if m:
                    session_id = m.group(1)

        text = generateReasoningResponse(userMessage, session_id=session_id, history=request.messages)
        thinking, content = _split_thinking(text)

        import time
        import uuid

        completionId = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())
        modelName = request.model or "tinytot"

        if request.stream:

            async def _sse_stream():
                if thinking:
                    think_chunk = {
                        "id": completionId,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": modelName,
                        "choices": [{"index": 0, "delta": {"reasoning_content": thinking}, "finish_reason": None}],
                    }
                    yield f"data: {json.dumps(think_chunk)}\n\n"
                words = content.split()
                for word in words:
                    chunk = {
                        "id": completionId,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": modelName,
                        "choices": [{"index": 0, "delta": {"content": f"{word} "}, "finish_reason": None}],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                done_chunk = {
                    "id": completionId,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": modelName,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(done_chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(_sse_stream(), media_type="text/event-stream")

        message_dict: dict = {"role": "assistant", "content": content}
        if thinking:
            message_dict["reasoning_content"] = thinking

        return {
            "id": completionId,
            "object": "chat.completion",
            "created": created,
            "model": modelName,
            "choices": [
                {
                    "index": 0,
                    "message": message_dict,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(userMessage.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(userMessage.split()) + len(content.split()),
            },
        }
    except Exception as e:
        logger.error("OpenAI chat error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/v1/models")
async def openai_models():
    """OpenAI-compatible model list endpoint."""
    import time

    return {
        "object": "list",
        "data": [
            {
                "id": "tinytot",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "tinytot",
            }
        ],
    }


@app.post("/api/quit")
@app.get("/api/quit")
async def quit_server():
    """Gracefully shut down the server."""
    import asyncio
    import os
    import signal

    logger.info("Shutdown requested via /api/quit")
    asyncio.get_event_loop().call_later(0.1, lambda: os.kill(os.getpid(), signal.SIGTERM))
    return {"status": "shutting down"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    import argparse
    import signal
    import sys

    parser = argparse.ArgumentParser(
        prog="tinytot",
        description=f"TinyToT v{__version__} — Tree of Thoughts inference. "
        "No args: start server. -p: single-shot query.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  tinytot                        Start server on http://localhost:11434\n"
            "  tinytot --port 8080            Start server on port 8080\n"
            "  tinytot -p 'What is pi?'       Single-shot query, no server\n"
        ),
    )
    parser.add_argument(
        "-p",
        "--prompt",
        metavar="PROMPT",
        help="Run a single prompt and print the response (non-interactive, no server started)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        metavar="PORT",
        help=f"Server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        metavar="HOST",
        help=f"Server host (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"TinyToT v{__version__}",
    )
    args = parser.parse_args()

    if args.prompt:
        from .inference import generateReasoningResponse

        print(generateReasoningResponse(args.prompt))
        sys.exit(0)

    print(f"TinyToT v{__version__} — http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
