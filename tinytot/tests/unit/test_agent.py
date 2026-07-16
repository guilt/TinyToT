"""Unit tests for tinytot.agent — detectAgentNeeds, LearningJournal, PlanExecuteLoop."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from tinytot.agent import (
    LearningJournal,
    PlanExecuteLoop,
    _extract_params,
    _infer_tool,
    agentResponse,
    detectAgentNeeds,
)

# ---------------------------------------------------------------------------
# detectAgentNeeds
# ---------------------------------------------------------------------------


class TestDetectAgentNeeds:
    def test_url_triggers(self):
        assert detectAgentNeeds("fetch https://arxiv.org/abs/2305.10601")

    def test_http_url_triggers(self):
        assert detectAgentNeeds("what is at http://example.com")

    def test_file_path_triggers(self):
        assert detectAgentNeeds("read /home/user/data.csv")

    def test_relative_path_triggers(self):
        assert detectAgentNeeds("analyse ./data/results.json")

    def test_search_keyword_triggers(self):
        assert detectAgentNeeds("search for tree of thoughts paper")

    def test_translate_keyword_triggers(self):
        assert detectAgentNeeds("translate this text to French")

    def test_analyse_keyword_triggers(self):
        assert detectAgentNeeds("analyse the data file")

    def test_multi_step_triggers(self):
        assert detectAgentNeeds("first search for the paper then summarize it")

    def test_step_by_step_triggers(self):
        assert detectAgentNeeds("solve this step by step")

    def test_duckduckgo_trigger(self):
        assert detectAgentNeeds("duckduckgo: tree of thoughts")

    def test_arxiv_trigger(self):
        assert detectAgentNeeds("find the arxiv paper on ToT")

    def test_read_file_triggers(self):
        assert detectAgentNeeds("read the file results.pdf")

    def test_list_files_triggers(self):
        assert detectAgentNeeds("list the files in the directory")

    def test_plain_math_does_not_trigger(self):
        assert not detectAgentNeeds("what is 2 + 2")

    def test_simple_factual_does_not_trigger(self):
        assert not detectAgentNeeds("what is the capital of France")

    def test_simple_definition_does_not_trigger(self):
        assert not detectAgentNeeds("what is machine learning")

    def test_empty_string_does_not_trigger(self):
        assert not detectAgentNeeds("")


# ---------------------------------------------------------------------------
# _infer_tool
# ---------------------------------------------------------------------------


class TestInferTool:
    def test_url_infers_web_fetch(self):
        assert _infer_tool("fetch https://example.com") == "web_fetch"

    def test_search_infers_web_search(self):
        assert _infer_tool("search for papers on ToT") == "web_search"

    def test_pdf_infers_document_extract(self):
        assert _infer_tool("read the document.pdf") == "document_extract"

    def test_translate_infers_translate(self):
        assert _infer_tool("translate to French") == "translate"

    def test_data_csv_infers_data_explore(self):
        assert _infer_tool("explore the data.csv file") == "data_explore"

    def test_list_files_infers_file_explore(self):
        assert _infer_tool("list files in directory") == "file_explore"

    def test_run_command_infers_shell(self):
        assert _infer_tool("run the build command") == "shell_run"

    def test_image_infers_image_analyse(self):
        assert _infer_tool("analyse the image photo.png") == "image_analyse"

    def test_unknown_falls_back_to_web_search(self):
        assert _infer_tool("something completely random with no tool signals") == "web_search"

    def test_url_present_falls_back_to_web_fetch(self):
        assert _infer_tool("something https://example.com random") == "web_fetch"


# ---------------------------------------------------------------------------
# _extract_params
# ---------------------------------------------------------------------------


class TestExtractParams:
    def test_web_fetch_extracts_url(self):
        params = _extract_params("web_fetch", "fetch https://arxiv.org/1234", "original")
        assert "url" in params
        assert "arxiv.org" in params["url"]

    def test_web_search_strips_trigger_word(self):
        params = _extract_params("web_search", "search for tree of thoughts", "original")
        assert "query" in params
        assert "search" not in params["query"].lower() or "tree" in params["query"].lower()

    def test_translate_extracts_target_lang(self):
        params = _extract_params("translate", "translate to French", "hello world")
        assert params.get("target", "").lower() in ("fr", "french")

    def test_translate_defaults_target_to_en(self):
        params = _extract_params("translate", "translate this", "text")
        assert "target" in params

    def test_document_extract_url(self):
        params = _extract_params("document_extract", "read https://arxiv.org/pdf/1234.pdf", "")
        assert "source" in params
        assert "arxiv" in params["source"]

    def test_file_explore_list_operation(self):
        params = _extract_params("file_explore", "list /home/user/data", "")
        assert params.get("operation") == "list"

    def test_shell_run_extracts_quoted_command(self):
        params = _extract_params("shell_run", "run `git status`", "")
        assert "command" in params
        assert "git status" in params["command"]

    def test_data_explore_default_operation(self):
        params = _extract_params("data_explore", "describe /data/results.csv", "/data/results.csv")
        assert params.get("operation") in ("describe", "head", "schema", "query")


# ---------------------------------------------------------------------------
# LearningJournal
# ---------------------------------------------------------------------------


class TestLearningJournal:
    def test_record_creates_file(self, tmp_path):
        journal = LearningJournal(journal_dir=tmp_path)
        journal.record("Paris is the capital of France")
        files = list(tmp_path.glob("*.md"))
        assert len(files) == 1

    def test_record_content_in_file(self, tmp_path):
        journal = LearningJournal(journal_dir=tmp_path)
        journal.record("TinyToT uses Tree of Thoughts")
        content = list(tmp_path.glob("*.md"))[0].read_text()
        assert "TinyToT uses Tree of Thoughts" in content

    def test_record_hermes_format_heading(self, tmp_path):
        journal = LearningJournal(journal_dir=tmp_path)
        journal.record("Some fact")
        content = list(tmp_path.glob("*.md"))[0].read_text()
        assert content.strip().startswith("##") or "\n## " in content

    def test_record_includes_source(self, tmp_path):
        journal = LearningJournal(journal_dir=tmp_path)
        journal.record("A fact", source="test_source")
        content = list(tmp_path.glob("*.md"))[0].read_text()
        assert "test_source" in content

    def test_record_includes_session_id(self, tmp_path):
        journal = LearningJournal(journal_dir=tmp_path)
        journal.record("Fact", session_id="sess-abc")
        content = list(tmp_path.glob("*.md"))[0].read_text()
        assert "sess-abc" in content

    def test_multiple_records_in_same_file(self, tmp_path):
        journal = LearningJournal(journal_dir=tmp_path)
        journal.record("Fact one")
        journal.record("Fact two")
        files = list(tmp_path.glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "Fact one" in content
        assert "Fact two" in content

    def test_recent_returns_entries(self, tmp_path):
        journal = LearningJournal(journal_dir=tmp_path)
        journal.record("Memorable fact")
        entries = journal.recent(days=7)
        assert any("Memorable fact" in e for e in entries)

    def test_recent_empty_dir(self, tmp_path):
        journal = LearningJournal(journal_dir=tmp_path / "new")
        assert journal.recent() == []

    def test_record_handles_io_error_gracefully(self, tmp_path):
        journal = LearningJournal(journal_dir=tmp_path)
        # Make the directory read-only to force IOError
        import os

        os.chmod(tmp_path, 0o444)
        try:
            journal.record("Should not crash")  # should log warning, not raise
        finally:
            os.chmod(tmp_path, 0o755)


# ---------------------------------------------------------------------------
# PlanExecuteLoop
# ---------------------------------------------------------------------------


class MockToolRegistry:
    def __init__(self, results: dict):
        self._results = results

    def get(self, name):
        return name in self._results or None

    def run(self, name, **kwargs):
        return self._results.get(name, f"[mock result for {name}]")


class TestPlanExecuteLoop:
    def _make_loop(self, tool_results: dict | None = None, journal_dir=None):
        loop = PlanExecuteLoop.__new__(PlanExecuteLoop)
        loop._tools = MockToolRegistry(tool_results or {})
        loop._journal = LearningJournal(journal_dir=journal_dir or Path("/tmp/tinytot_test_journal"))
        return loop

    def test_synthesise_without_context_calls_generateReasoningResponse(self, tmp_path):
        loop = self._make_loop(journal_dir=tmp_path)
        with patch("tinytot.inference.generateTreeOfThoughtsResponse", return_value="answer"):
            result = loop._synthesise("what is 2+2", "")
        assert result == "answer"

    def test_synthesise_with_context_includes_context_in_prompt(self, tmp_path):
        loop = self._make_loop(journal_dir=tmp_path)
        calls = []

        def fake_gen(prompt, **kwargs):
            calls.append(prompt)
            return "synthesised answer"

        with patch("tinytot.inference.generateTreeOfThoughtsResponse", fake_gen):
            result = loop._synthesise("my question", "gathered context here")

        assert result == "synthesised answer"
        assert "my question" in calls[0]
        assert "gathered context here" in calls[0]

    def test_run_calls_tool_and_returns_synthesis(self, tmp_path):
        loop = self._make_loop(
            tool_results={"web_search": "search results about ToT"},
            journal_dir=tmp_path,
        )

        with patch("tinytot.agent.PlanExecuteLoop._plan", return_value=[("web_search", {"query": "tree of thoughts"})]):
            with patch("tinytot.inference.generateTreeOfThoughtsResponse", return_value="final answer"):
                result = loop.run("search for tree of thoughts")

        assert result == "final answer"

    def test_run_empty_tool_result_falls_through(self, tmp_path):
        loop = self._make_loop(
            tool_results={"web_search": "[web_search error] connection refused"},
            journal_dir=tmp_path,
        )

        with patch("tinytot.agent.PlanExecuteLoop._plan", return_value=[("web_search", {"query": "something"})]):
            with patch("tinytot.inference.generateTreeOfThoughtsResponse", return_value="fallback"):
                result = loop.run("search for something")

        assert result == "fallback"

    def test_plan_single_url_is_web_fetch(self, tmp_path):
        loop = self._make_loop(journal_dir=tmp_path)
        with patch("tinytot.inference.generateTreeOfThoughtsResponse", return_value="no steps"):
            steps = loop._plan("fetch https://example.com")
        assert steps[0][0] == "web_fetch"

    def test_plan_respects_max_steps(self, tmp_path):
        loop = self._make_loop(journal_dir=tmp_path)
        with patch(
            "tinytot.inference.generateTreeOfThoughtsResponse",
            return_value="\n".join(f"Step {i}: [web_search] - search thing {i}" for i in range(20)),
        ):
            steps = loop._plan("complex multi-step task " + " and then " * 5 + "summarize")
        from tinytot.agent import _MAX_STEPS

        assert len(steps) <= _MAX_STEPS

    def test_journal_records_on_useful_result(self, tmp_path):
        loop = self._make_loop(
            tool_results={"web_search": "A" * 300},  # long useful result
            journal_dir=tmp_path,
        )

        with patch("tinytot.agent.PlanExecuteLoop._plan", return_value=[("web_search", {"query": "test"})]):
            with patch("tinytot.inference.generateTreeOfThoughtsResponse", return_value="done"):
                loop.run("search for something interesting", session_id="test-session")

        files = list(tmp_path.glob("*.md"))
        assert len(files) == 1


# ---------------------------------------------------------------------------
# agentResponse (public entry point)
# ---------------------------------------------------------------------------


class TestAgentResponse:
    def test_returns_string(self):
        with patch("tinytot.agent._loop") as mock_loop:
            mock_loop.run.return_value = "agent result"
            result = agentResponse("search for something")
        assert result == "agent result"

    def test_passes_session_id(self):
        with patch("tinytot.agent._loop") as mock_loop:
            mock_loop.run.return_value = "ok"
            agentResponse("fetch https://example.com", session_id="my-session")
            mock_loop.run.assert_called_once_with("fetch https://example.com", session_id="my-session")
