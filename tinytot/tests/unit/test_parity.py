"""Tests for tinytot.parity — reasoning parity analysis over opencode exports."""

import json

from tinytot.parity import (
    TraceStep,
    crossProviderReport,
    encryptedBlocks,
    extractedTokens,
    fidelityReport,
    modelFamily,
    parseExport,
    parseExports,
    routingReport,
    stepFidelity,
    taskKey,
)


def _export(
    model: str = "claude-opus-4-8",
    task: str = "Write a Python function.",
    reasoning: str = "Need a median function. Sort then pick middle.",
    output: str = "def median(xs): ...",
    reasoning_tokens: int = 0,
    reasoning_meta=None,
) -> dict:
    parts = [
        {"type": "step-start"},
    ]
    if reasoning or reasoning_tokens or reasoning_meta:
        part = {"type": "reasoning", "text": reasoning}
        if reasoning_meta:
            part["metadata"] = reasoning_meta
        parts.append(part)
    if output:
        parts.append({"type": "text", "text": output})
    parts.append(
        {
            "type": "step-finish",
            "tokens": {"input": 10, "output": 5, "reasoning": reasoning_tokens, "cache": {"read": 0, "write": 0}},
            "cost": 0.01,
        }
    )
    return {
        "info": {
            "id": "ses_test123",
            "slug": "sluggy",
            "title": "Test title",
            "model": {"id": model, "providerID": "opencode", "variant": "high"},
            "tokens": {"input": 10, "output": 5, "reasoning": reasoning_tokens},
            "cost": 0.01,
        },
        "messages": [
            {
                "info": {"role": "user", "time": {"created": 1}},
                "parts": [{"type": "text", "text": task}],
            },
            {
                "info": {
                    "role": "assistant",
                    "modelID": model,
                    "providerID": "opencode",
                    "tokens": {"input": 10, "output": 5, "reasoning": reasoning_tokens},
                    "cost": 0.01,
                },
                "parts": parts,
            },
        ],
    }


# ---------------------------------------------------------------------------
# parseExport / parseExports
# ---------------------------------------------------------------------------


class TestParseExport:
    def test_extracts_task_model_and_steps(self):
        tr = parseExport(_export(reasoning="Some long reasoning text here for extraction."))
        assert tr.session_id == "ses_test123"
        assert tr.model == "claude-opus-4-8"
        assert tr.provider == "opencode"
        assert "Python function" in tr.task
        assert len(tr.steps) == 1
        assert "extraction" in tr.steps[0].reasoning
        assert tr.steps[0].tokens["reasoning"] == 0

    def test_captures_reasoning_meta(self):
        meta = {"openai": {"itemId": "rs_123", "reasoningEncryptedContent": "AAAAbbbb"}}
        tr = parseExport(_export(reasoning="", reasoning_tokens=42, reasoning_meta=meta))
        assert tr.steps[0].reasoning_meta == meta

    def test_parse_exports_dir(self, tmp_path):
        (tmp_path / "a.json").write_text(json.dumps(_export()), encoding="utf-8")
        (tmp_path / "b.txt").write_text("not json", encoding="utf-8")
        traces = parseExports(tmp_path)
        assert len(traces) == 1


# ---------------------------------------------------------------------------
# Shared metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    def test_extracted_tokens_counts_words(self):
        assert extractedTokens("one two three four") == 4
        assert extractedTokens("") == 0

    def test_task_key_normalises(self):
        a = taskKey("Write a  Python function.")
        b = taskKey("write a python function.")
        assert a == b
        assert taskKey("different") != a

    def test_model_family(self):
        assert modelFamily("claude-haiku-4-5") == "anthropic"
        assert modelFamily("gpt-5.6-luna") == "openai"
        assert modelFamily("gemini-3-flash") == "google"
        assert modelFamily("grok-4.6") == "xai"
        assert modelFamily("deepseek-v4-flash") == "deepseek"
        assert modelFamily("weird-unknown") == "other"


class TestStepFidelity:
    def test_ratio_when_reported(self):
        step = TraceStep(
            reasoning="alpha beta gamma delta", output="", tokens={"reasoning": 4}, cost=0, model="", provider=""
        )
        fid, opaque = stepFidelity(step)
        assert fid == 1.0
        assert not opaque

    def test_none_when_unreported_but_text(self):
        step = TraceStep(
            reasoning="alpha beta gamma", output="", tokens={"reasoning": 0}, cost=0, model="", provider=""
        )
        assert stepFidelity(step) == (None, False)

    def test_opaque_when_reported_but_no_text(self):
        step = TraceStep(reasoning="", output="", tokens={"reasoning": 99}, cost=0, model="", provider="")
        fid, opaque = stepFidelity(step)
        assert fid == 0.0
        assert opaque


class TestEncryptedBlocks:
    def test_extracts_encrypted_content(self):
        step = TraceStep(
            reasoning="summary",
            output="",
            tokens={},
            cost=0,
            model="",
            provider="",
            reasoning_meta={"openai": {"itemId": "rs_1", "reasoningEncryptedContent": "cipher"}},
        )
        blocks = encryptedBlocks(step)
        assert len(blocks) == 1
        assert blocks[0]["vendor"] == "openai"
        assert blocks[0]["block_chars"] == 6
        assert blocks[0]["has_summary"] is True

    def test_empty_when_no_metadata(self):
        step = TraceStep(reasoning="", output="", tokens={}, cost=0, model="", provider="")
        assert encryptedBlocks(step) == []


# ---------------------------------------------------------------------------
# fidelityReport
# ---------------------------------------------------------------------------


class TestFidelityReport:
    def test_inventories_encrypted_and_opaque(self):
        traces = [
            parseExport(
                _export(
                    model="gpt-5.6-luna",
                    reasoning="",
                    reasoning_tokens=100,
                    reasoning_meta={"openai": {"itemId": "rs_x", "reasoningEncryptedContent": "blob"}},
                )
            ),
            parseExport(_export(model="claude-haiku-4-5", reasoning="", reasoning_tokens=0)),
            parseExport(
                _export(model="deepseek-v4-flash-free", reasoning="plaintext reasoning here", reasoning_tokens=0)
            ),
        ]
        report = fidelityReport(traces)
        s = report["summary"]
        assert s["encrypted_block_count"] == 1
        assert s["opaque_count"] == 1
        assert s["unreported_reasoning_steps"] == 1
        assert s["steps_with_reported"] == 1
        assert report["encrypted_blocks"][0]["family"] == "openai"
        assert report["family_fidelity"]  # openai family has one fidelity value

    def test_fidelity_ratio(self):
        traces = [parseExport(_export(reasoning="alpha beta gamma delta epsilon zeta eta theta", reasoning_tokens=8))]
        report = fidelityReport(traces)
        assert report["summary"]["mean_fidelity"] == 1.0


# ---------------------------------------------------------------------------
# crossProviderReport
# ---------------------------------------------------------------------------


class TestCrossProviderReport:
    def test_groups_by_task_and_reports_overlap(self):
        task = "Same exact task prompt."
        t1 = parseExport(
            _export(model="gpt-5.6-luna", task=task, reasoning="alpha beta gamma delta", reasoning_tokens=4)
        )
        t2 = parseExport(_export(model="claude-haiku-4-5", task=task, reasoning="", reasoning_tokens=0))
        report = crossProviderReport([t1, t2])
        assert len(report["tasks"]) == 1
        task_group = report["tasks"][0]
        assert {m["model"] for m in task_group["models"]} == {"gpt-5.6-luna", "claude-haiku-4-5"}
        pair = task_group["pairs"][0]
        assert pair["reasoning_jaccard"] == 0.0  # claude has no reasoning

    def test_empty_vs_empty_is_none(self):
        task = "Another task."
        t1 = parseExport(_export(task=task, reasoning="", reasoning_tokens=0))
        t2 = parseExport(_export(task=task, reasoning="", reasoning_tokens=0))
        report = crossProviderReport([t1, t2])
        assert report["tasks"][0]["pairs"][0]["reasoning_jaccard"] is None


# ---------------------------------------------------------------------------
# routingReport
# ---------------------------------------------------------------------------


class TestRoutingReport:
    def test_python_task_routes_to_programming(self, category_dir):
        from tinytot.retrieval import buildChainIndex, buildChainMeta

        buildChainIndex.cache_clear()
        buildChainMeta.cache_clear()
        try:
            tr = parseExport(_export(task="Write a Python function that computes the median."))
            report = routingReport([tr], category_dir)
            assert report["summary"]["total"] == 1
            row = report["rows"][0]
            assert row["expected_category"] == "programming"
            assert "match" in row
        finally:
            buildChainIndex.cache_clear()
            buildChainMeta.cache_clear()

    def test_rate_word_problem_routes_to_math(self, category_dir):
        from tinytot.retrieval import buildChainIndex, buildChainMeta

        buildChainIndex.cache_clear()
        buildChainMeta.cache_clear()
        try:
            tr = parseExport(
                _export(
                    task=(
                        "A train leaves Station A at 2:00 PM traveling at 60 mph toward Station B, "
                        "which is 150 miles away. Another train leaves Station B at 2:30 PM traveling "
                        "at 50 mph toward Station A. At what clock time do the two trains meet?"
                    )
                )
            )
            report = routingReport([tr], category_dir)
            row = report["rows"][0]
            assert row["routed_category"] == "math"
            assert row["expected_category"] == "math"
            assert row["match"] is True
        finally:
            buildChainIndex.cache_clear()
            buildChainMeta.cache_clear()


class TestMainCli:
    def test_cli_runs_fidelity_subcommand(self, tmp_path, capsys, monkeypatch):
        (tmp_path / "a.json").write_text(json.dumps(_export()), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["parity", str(tmp_path), "fidelity", "--json"])
        import tinytot.parity as parity

        parity.main()
        out = capsys.readouterr().out
        assert "mean_fidelity" in out

    def test_cli_runs_all_subcommand(self, tmp_path, capsys, monkeypatch, category_dir):
        (tmp_path / "a.json").write_text(json.dumps(_export()), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["parity", str(tmp_path), "all", "--category-dir", str(category_dir)])
        import tinytot.parity as parity

        parity.main()
        out = capsys.readouterr().out
        assert "Routing parity" in out
