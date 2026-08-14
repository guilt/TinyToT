"""Tests for tinytot.ingest — OpenCode trace ingestion and task classification."""

import argparse
import json
from pathlib import Path

import pytest

from tinytot.ingest import (
    OpenCodeSource,
    _classifyTaskDomain,
    _opencodeChain,
    _opencodeSteps,
    _opencodeTask,
    ingestOpenCode,
)

TASK = "The function total(xs) is supposed to return the sum of a list but the empty-list case has a bug."

EXPORT = {
    "info": {
        "id": "ses_unit1",
        "slug": "unit-test",
        "title": "Fix sum bug",
        "model": {"id": "grok-4.6", "providerID": "opencode", "variant": "high"},
        "tokens": {"input": 500, "output": 40, "reasoning": 100},
        "cost": 0.01,
    },
    "messages": [
        {
            "info": {"role": "user", "time": {"created": 1}},
            "parts": [{"type": "text", "text": TASK}],
        },
        {
            "info": {
                "role": "assistant",
                "modelID": "grok-4.6",
                "providerID": "opencode",
                "tokens": {"input": 500, "output": 40, "reasoning": 100},
                "cost": 0.01,
            },
            "parts": [
                {"type": "step-start"},
                {"type": "reasoning", "text": "Inspect the function to find the empty-list bug."},
                {"type": "text", "text": "Initialize s = 0."},
                {"type": "step-finish"},
            ],
        },
    ],
}

DEBUG_MD = """\
---
category: debug
keywords: debug, bug, fix, error, traceback
---

# Debug
"""


def _write_export(d: Path, name: str, data: dict) -> Path:
    f = d / name
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# _classifyTaskDomain — word-boundary matching regression tests
# ---------------------------------------------------------------------------


class TestClassifyTaskDomain:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Write a Python function that computes the median", "python"),
            ("Explain the likely bug and the fix in one short paragraph", "debugging"),
            ("A train leaves Station A at 2:00 PM traveling at 60 mph", "math"),
            ("important report about the port migration", "migration"),
            ("explain how planes fly", "general"),
            ("its typescript file has js errors", "javascript"),
            ("sort this array and search for a tree in a graph", "algorithms"),
            ("dockerize the container and deploy with k8s", "devops"),
        ],
    )
    def test_word_boundaries(self, text, expected):
        assert _classifyTaskDomain(text) == expected

    def test_prefix_suffix_containing_fix_is_debug(self):
        assert _classifyTaskDomain("suffix prefix affix all contain fix") == "debugging"


# ---------------------------------------------------------------------------
# OpenCode trace parsing helpers
# ---------------------------------------------------------------------------


class TestOpenCodeParsing:
    def test_task_extracts_user_text(self):
        task = _opencodeTask(EXPORT)
        assert isinstance(task, str)
        assert "total(xs)" in task

    def test_steps_capture_reasoning_and_tokens(self):
        steps = _opencodeSteps(EXPORT)
        assert len(steps) == 1
        s = steps[0]
        assert s["reasoning"] == "Inspect the function to find the empty-list bug."
        assert s["output"] == "Initialize s = 0."
        assert s["reasoning_meta"] == {}
        assert s["tokens"] == {"input": 500, "output": 40, "reasoning": 100}
        assert s["cost"] == 0.01
        assert s["model"] == "grok-4.6"

    def test_steps_skip_session_with_no_assistant(self):
        no_assistant = {**EXPORT, "messages": EXPORT["messages"][:1]}
        assert _opencodeSteps(no_assistant) == []

    def test_steps_capture_encrypted_meta(self):
        enc = json.loads(json.dumps(EXPORT))
        enc["messages"][1]["parts"][1]["metadata"] = {"openai": {"itemId": "rs_x", "reasoningEncryptedContent": "blob"}}
        steps = _opencodeSteps(enc)
        assert steps[0]["reasoning_meta"]["openai"]["itemId"] == "rs_x"


# ---------------------------------------------------------------------------
# _opencodeChain — chain text construction
# ---------------------------------------------------------------------------


class TestOpenCodeChain:
    def test_builds_chain_with_trace_metadata(self):
        task = _opencodeTask(EXPORT)
        steps = _opencodeSteps(EXPORT)
        chain = _opencodeChain(EXPORT, task, steps, 1)
        assert chain is not None
        assert "## Chain 1:" in chain
        assert "Thought 1:" in chain
        assert "Conclusion:" in chain
        assert "<!-- trace: {" in chain
        assert "<!-- Handles:" in chain
        assert '"model":"grok-4.6"' in chain
        assert '"reasoning":100' in chain

    def test_returns_none_when_no_reasoning(self):
        no_reasoning = json.loads(json.dumps(EXPORT))
        no_reasoning["messages"][1]["parts"] = [
            {"type": "step-start"},
            {"type": "text", "text": "plain answer"},
            {"type": "step-finish"},
        ]
        no_reasoning["messages"][1]["info"]["tokens"]["reasoning"] = 0
        no_reasoning["info"]["tokens"]["reasoning"] = 0
        task = _opencodeTask(no_reasoning)
        steps = _opencodeSteps(no_reasoning)
        assert _opencodeChain(no_reasoning, task, steps, 1) is None

    def test_withheld_reasoning_creates_thought(self):
        opaque = json.loads(json.dumps(EXPORT))
        opaque["messages"][1]["parts"] = [
            {"type": "step-start"},
            {"type": "text", "text": "plain answer"},
            {"type": "step-finish"},
        ]
        task = _opencodeTask(opaque)
        steps = _opencodeSteps(opaque)
        chain = _opencodeChain(opaque, task, steps, 1)
        assert chain is not None
        assert "Reasoning withheld" in chain
        assert "100" in chain


# ---------------------------------------------------------------------------
# ingestOpenCode — end-to-end write
# ---------------------------------------------------------------------------


class TestIngestOpenCode:
    def test_writes_augment_files_into_matching_category(self, tmp_path):
        src = tmp_path / "exports"
        src.mkdir()
        _write_export(src, "unit1.json", EXPORT)
        out_dir = tmp_path / "categories"
        out_dir.mkdir()
        (out_dir / "debug.md").write_text(DEBUG_MD, encoding="utf-8")

        results = ingestOpenCode(src, out_dir)
        assert results == {"opencode_augment_debug": 1}
        target = out_dir / "opencode_augment_debug.md"
        assert target.exists()
        text = target.read_text(encoding="utf-8")
        assert "## Chain 1:" in text
        assert "ses_unit1" in text
        assert "grok-4.6" in text

    def test_runs_through_source(self, tmp_path, monkeypatch):
        import tinytot.ingest as ingest_mod

        src = tmp_path / "exports"
        src.mkdir()
        _write_export(src, "unit2.json", EXPORT)
        out_dir = tmp_path / "categories"
        out_dir.mkdir()
        (out_dir / "debug.md").write_text(DEBUG_MD, encoding="utf-8")
        monkeypatch.setattr(ingest_mod, "CATEGORY_DIR", out_dir)

        args = argparse.Namespace(dir=src, session=None, limit=0, max_chains=10000)
        results = OpenCodeSource().run(args)
        assert results == [("opencode_augment_debug", 1, out_dir / "opencode_augment_debug.md")]
