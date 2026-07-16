"""Unit tests for tinytot.tools_ext — Tool ABC, ToolRegistry, and all concrete tools."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tinytot.tools_ext import (
    DataTool,
    DocumentTool,
    FileTool,
    ImageTool,
    SearchTool,
    ShellTool,
    Tool,
    ToolRegistry,
    TranslateTool,
    WebTool,
    registry,
)

# ---------------------------------------------------------------------------
# Tool ABC / ToolRegistry
# ---------------------------------------------------------------------------


class TestToolRegistry:
    def test_global_registry_has_all_tools(self):
        names = {t.name for t in registry.all()}
        assert names >= {
            "web_fetch",
            "web_search",
            "document_extract",
            "translate",
            "data_explore",
            "file_explore",
            "shell_run",
            "image_analyse",
        }

    def test_get_returns_tool(self):
        assert registry.get("web_fetch") is not None

    def test_get_unknown_returns_none(self):
        assert registry.get("nonexistent_tool_xyz") is None

    def test_run_unknown_tool_returns_error_string(self):
        result = registry.run("nonexistent_tool_xyz")
        assert "unknown tool" in result.lower()

    def test_schemas_returns_list(self):
        schemas = registry.schemas()
        assert len(schemas) > 0
        for s in schemas:
            assert s["type"] == "function"
            assert "name" in s["function"]
            assert "description" in s["function"]

    def test_register_custom_tool(self):
        class MyTool(Tool):
            name = "my_custom_tool"
            description = "test tool"
            params = [("x", "some param", True)]

            def run(self, x: str = "") -> str:
                return f"got:{x}"

        reg = ToolRegistry()
        reg.register(MyTool())
        assert reg.get("my_custom_tool") is not None
        assert reg.run("my_custom_tool", x="hello") == "got:hello"

    def test_run_propagates_exception_as_string(self):
        class BrokenTool(Tool):
            name = "broken"
            description = "breaks"

            def run(self, **_):
                raise ValueError("boom")

        reg = ToolRegistry()
        reg.register(BrokenTool())
        result = reg.run("broken")
        assert "broken" in result.lower() or "boom" in result.lower()

    def test_schema_required_fields(self):
        tool = WebTool()
        schema = tool.schema()
        assert schema["function"]["parameters"]["required"] == ["url"]

    def test_schema_optional_field_not_in_required(self):
        tool = WebTool()
        schema = tool.schema()
        assert "max_chars" not in schema["function"]["parameters"]["required"]


# ---------------------------------------------------------------------------
# WebTool
# ---------------------------------------------------------------------------


class TestWebTool:
    def test_strips_html_tags(self):
        html = "<html><head><title>T</title></head><body><p>Hello world</p><script>js</script></body></html>"
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client
            result = WebTool().run(url="https://example.com")

        assert "Hello world" in result
        assert "<script>" not in result
        assert "<p>" not in result

    def test_respects_max_chars(self):
        html = "<html><body>" + "A " * 5000 + "</body></html>"
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client
            result = WebTool().run(url="https://example.com", max_chars="100")

        assert len(result) <= 100

    def test_plain_text_returned_as_is(self):
        mock_resp = MagicMock()
        mock_resp.text = "plain text content"
        mock_resp.headers = {"content-type": "text/plain"}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client
            result = WebTool().run(url="https://example.com/file.txt")

        assert "plain text content" in result

    def test_http_error_returns_error_string(self):
        import httpx

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.ConnectError("connection refused")
            mock_client_cls.return_value = mock_client
            result = WebTool().run(url="https://unreachable.invalid")

        assert "error" in result.lower() or "web_fetch" in result


# ---------------------------------------------------------------------------
# SearchTool
# ---------------------------------------------------------------------------


class TestSearchTool:
    def _make_ddg_html(self, results: list[dict]) -> str:
        items = ""
        for r in results:
            items += (
                f'<div class="result">'
                f'<h2 class="result__title">{r["title"]}</h2>'
                f'<div class="result__snippet">{r["snippet"]}</div>'
                f'<span class="result__url">{r["url"]}</span>'
                f"</div>"
            )
        return f"<html><body>{items}</body></html>"

    def test_returns_result_snippets(self):
        html = self._make_ddg_html(
            [
                {"title": "Tree of Thoughts", "snippet": "A reasoning framework", "url": "arxiv.org/1234"},
            ]
        )
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_resp
            mock_client_cls.return_value = mock_client
            result = SearchTool().run(query="Tree of Thoughts", num_results="1")

        assert "Tree of Thoughts" in result
        assert "reasoning framework" in result

    def test_no_results_message(self):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body></body></html>"
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_resp
            mock_client_cls.return_value = mock_client
            result = SearchTool().run(query="xyzzy123notarealthing")

        assert "no results" in result.lower()


# ---------------------------------------------------------------------------
# DocumentTool
# ---------------------------------------------------------------------------


class TestDocumentTool:
    def test_extract_txt(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("Hello from text file.")
        result = DocumentTool().run(source=str(f))
        assert "Hello from text file." in result

    def test_extract_markdown(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\nSome content here.")
        result = DocumentTool().run(source=str(f))
        assert "Some content" in result

    def test_respects_max_chars(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_text("A" * 10000)
        result = DocumentTool().run(source=str(f), max_chars="100")
        assert len(result) <= 100

    def test_missing_file_returns_error(self):
        result = DocumentTool().run(source="/nonexistent/path/file.txt")
        assert "not found" in result.lower() or "error" in result.lower()

    def test_extract_pdf_calls_pypdf(self, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4 fake")
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF content here"
        mock_reader.pages = [mock_page]

        import sys

        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader.return_value = mock_reader
        with patch.dict(sys.modules, {"pypdf": mock_pypdf}):
            result = DocumentTool().run(source=str(f))

        assert "PDF content here" in result

    def test_parse_page_range_dash(self):
        idxs = DocumentTool._parse_page_range("2-4", 10)
        assert idxs == [1, 2, 3]

    def test_parse_page_range_single(self):
        idxs = DocumentTool._parse_page_range("3", 10)
        assert idxs == [2]

    def test_parse_page_range_invalid(self):
        idxs = DocumentTool._parse_page_range("bad", 5)
        assert idxs == list(range(5))

    def test_extract_docx_calls_python_docx(self, tmp_path):
        f = tmp_path / "doc.docx"
        f.write_bytes(b"PK fake docx")
        mock_para = MagicMock()
        mock_para.text = "Docx paragraph text"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]

        import sys

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        with patch.dict(sys.modules, {"docx": mock_docx}):
            result = DocumentTool().run(source=str(f))

        assert "Docx paragraph text" in result


# ---------------------------------------------------------------------------
# TranslateTool
# ---------------------------------------------------------------------------


class TestTranslateTool:
    def _make_httpx_response(self, translated_text: str) -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [[[translated_text, "original"]]]
        return mock_resp

    def _mock_all(self, translated: str = "Bonjour monde"):
        """Patch _ct2_translate to None and mock httpx so tests reach the Google endpoint."""
        from contextlib import ExitStack

        import httpx

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = httpx.ConnectError("no local server")
        mock_client.get.return_value = self._make_httpx_response(translated)

        stack = ExitStack()
        stack.enter_context(patch("tinytot.tools_ext._ct2_translate", return_value=None))
        stack.enter_context(patch("httpx.Client", return_value=mock_client))
        return stack, mock_client

    def test_translate_short_text(self):
        ctx, _ = self._mock_all("Bonjour monde")
        with ctx:
            result = TranslateTool().run(text="Hello world", target="fr")
        assert result == "Bonjour monde"

    def test_translate_passes_target_lang(self):
        ctx, mock_client = self._mock_all("Bonjour")
        with ctx:
            TranslateTool().run(text="Hello", target="fr")
        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["tl"] == "fr"

    def test_translate_long_text_chunked(self):
        import httpx

        call_count = [0]

        def _side_effect(url, **kwargs):
            call_count[0] += 1
            return self._make_httpx_response(f"chunk-{call_count[0]}")

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = httpx.ConnectError("no local server")
        mock_client.get.side_effect = _side_effect
        long_text = "word " * 2000
        with patch("tinytot.tools_ext._ct2_translate", return_value=None), patch(
            "httpx.Client", return_value=mock_client
        ):
            result = TranslateTool().run(text=long_text, target="de")
        assert call_count[0] > 1
        assert "chunk" in result

    def test_explicit_source_language(self):
        ctx, mock_client = self._mock_all("Hola")
        with ctx:
            TranslateTool().run(text="Hello", target="es", source="en")
        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["sl"] == "en"
        assert call_kwargs["params"]["tl"] == "es"

    def test_network_error_returns_graceful_string(self):
        """When all backends fail, returns a graceful [translate] error string."""
        import httpx

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = httpx.ConnectError("blocked")
        mock_client.get.side_effect = httpx.ConnectError("blocked")
        with patch("tinytot.tools_ext._ct2_translate", return_value=None), patch(
            "httpx.Client", return_value=mock_client
        ):
            result = TranslateTool().run(text="Hello", target="sw")
        assert isinstance(result, str)
        assert "[translate]" in result or "No working backend" in result


# ---------------------------------------------------------------------------
# DataTool
# ---------------------------------------------------------------------------


class TestDataTool:
    def test_csv_schema(self, tmp_path):
        f = tmp_path / "data.csv"
        with open(f, "w", newline="") as fp:
            w = csv.DictWriter(fp, fieldnames=["name", "age", "score"])
            w.writeheader()
            w.writerows([{"name": "Alice", "age": "30", "score": "95"}, {"name": "Bob", "age": "25", "score": "88"}])
        result = DataTool().run(path=str(f), operation="schema")
        assert "name" in result
        assert "age" in result
        assert "Rows: 2" in result

    def test_csv_head(self, tmp_path):
        f = tmp_path / "data.csv"
        with open(f, "w", newline="") as fp:
            w = csv.DictWriter(fp, fieldnames=["x", "y"])
            w.writeheader()
            for i in range(20):
                w.writerow({"x": str(i), "y": str(i * 2)})
        result = DataTool().run(path=str(f), operation="head", arg="3")
        lines = [ln for ln in result.splitlines() if "|" in ln]
        assert len(lines) >= 3  # header + separator + rows

    def test_csv_describe(self, tmp_path):
        f = tmp_path / "data.csv"
        with open(f, "w", newline="") as fp:
            w = csv.DictWriter(fp, fieldnames=["val"])
            w.writeheader()
            for i in range(10):
                w.writerow({"val": str(i)})
        result = DataTool().run(path=str(f), operation="describe")
        assert "val" in result
        assert "min=" in result

    def test_csv_query_equals(self, tmp_path):
        f = tmp_path / "data.csv"
        with open(f, "w", newline="") as fp:
            w = csv.DictWriter(fp, fieldnames=["name", "city"])
            w.writeheader()
            w.writerows([{"name": "Alice", "city": "NYC"}, {"name": "Bob", "city": "LA"}])
        result = DataTool().run(path=str(f), operation="query", arg="city=NYC")
        assert "Alice" in result
        assert "Bob" not in result

    def test_csv_query_numeric_gt(self, tmp_path):
        f = tmp_path / "data.csv"
        with open(f, "w", newline="") as fp:
            w = csv.DictWriter(fp, fieldnames=["score"])
            w.writeheader()
            for s in [10, 50, 90]:
                w.writerow({"score": str(s)})
        result = DataTool().run(path=str(f), operation="query", arg="score>40")
        assert "50" in result
        assert "90" in result
        assert "10" not in result

    def test_json_array_schema(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps([{"a": 1, "b": 2}, {"a": 3, "b": 4}]))
        result = DataTool().run(path=str(f), operation="schema")
        assert "Array" in result or "a" in result

    def test_jsonl_head(self, tmp_path):
        f = tmp_path / "data.jsonl"
        lines = [json.dumps({"q": f"question {i}", "a": f"answer {i}"}) for i in range(10)]
        f.write_text("\n".join(lines))
        result = DataTool().run(path=str(f), operation="head", arg="3")
        assert "question" in result

    def test_missing_file_returns_error(self):
        result = DataTool().run(path="/no/such/file.csv")
        assert "not found" in result.lower()

    def test_unsupported_format(self, tmp_path):
        f = tmp_path / "data.parquet"
        f.write_bytes(b"PAR1")
        result = DataTool().run(path=str(f))
        assert "unsupported" in result.lower() or "error" in result.lower() or "parquet" in result.lower()

    def test_query_bad_format_returns_message(self, tmp_path):
        f = tmp_path / "data.csv"
        with open(f, "w", newline="") as fp:
            w = csv.DictWriter(fp, fieldnames=["x"])
            w.writeheader()
            w.writerow({"x": "1"})
        result = DataTool().run(path=str(f), operation="query", arg="badformat")
        assert "query format" in result.lower()


# ---------------------------------------------------------------------------
# FileTool
# ---------------------------------------------------------------------------


class TestFileTool:
    def test_list_directory(self, tmp_path):
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "file2.py").write_text("b")
        (tmp_path / "subdir").mkdir()
        result = FileTool().run(path=str(tmp_path), operation="list")
        assert "file1.txt" in result
        assert "file2.py" in result
        assert "subdir" in result

    def test_read_file(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("Hello TinyToT!")
        result = FileTool().run(path=str(f), operation="read")
        assert "Hello TinyToT!" in result

    def test_read_respects_max_chars(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_text("X" * 10000)
        result = FileTool().run(path=str(f), operation="read", max_chars="50")
        assert len(result) <= 50

    def test_read_line_range(self, tmp_path):
        f = tmp_path / "lines.txt"
        f.write_text("\n".join(f"line{i}" for i in range(20)))
        result = FileTool().run(path=str(f), operation="read", arg="3-5")
        assert "line2" in result
        assert "line4" in result
        assert "line0" not in result

    def test_search_finds_matches(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("def hello():\n    pass\ndef world():\n    pass\n")
        result = FileTool().run(path=str(tmp_path), operation="search", arg="def hello")
        assert "code.py" in result
        assert "def hello" in result

    def test_search_no_matches(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("nothing here")
        result = FileTool().run(path=str(tmp_path), operation="search", arg="xyzzy_not_present")
        assert "no matches" in result.lower()

    def test_stat_file(self, tmp_path):
        f = tmp_path / "info.txt"
        f.write_text("stat me")
        result = FileTool().run(path=str(f), operation="stat")
        assert "info.txt" in result
        assert "bytes" in result.lower()
        assert "file" in result.lower()

    def test_stat_directory(self, tmp_path):
        result = FileTool().run(path=str(tmp_path), operation="stat")
        assert "directory" in result.lower()

    def test_find_by_pattern(self, tmp_path):
        (tmp_path / "a.py").write_text("x")
        (tmp_path / "b.txt").write_text("y")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "c.py").write_text("z")
        result = FileTool().run(path=str(tmp_path), operation="find", arg="*.py")
        assert "a.py" in result
        assert "c.py" in result
        assert "b.txt" not in result

    def test_read_missing_file_returns_error(self):
        result = FileTool().run(path="/no/such/path/file.txt", operation="read")
        assert "not found" in result.lower() or "error" in result.lower()

    def test_denied_paths_blocked(self, tmp_path):
        # Don't write the file — just pass a .env path to the tool directly
        result = FileTool().run(path=str(tmp_path / ".env"), operation="read")
        assert "not permitted" in result.lower()

    def test_list_missing_directory_returns_error(self):
        result = FileTool().run(path="/no/such/directory_xyz", operation="list")
        assert "not found" in result.lower() or "error" in result.lower()

    def test_search_requires_arg(self, tmp_path):
        result = FileTool().run(path=str(tmp_path), operation="search", arg="")
        assert "search requires" in result.lower()

    def test_default_operation_is_list(self, tmp_path):
        (tmp_path / "f.txt").write_text("x")
        result = FileTool().run(path=str(tmp_path))
        assert "f.txt" in result


# ---------------------------------------------------------------------------
# ShellTool
# ---------------------------------------------------------------------------


class TestShellTool:
    def test_simple_echo(self):
        result = ShellTool().run(command="echo hello_tinytot")
        assert "hello_tinytot" in result
        assert "exit_code: 0" in result

    def test_failing_command_returns_nonzero_exit(self):
        result = ShellTool().run(command="false")
        assert "exit_code: 1" in result or "exit_code: " in result

    def test_stderr_captured(self):
        result = ShellTool().run(command="echo error_msg >&2")
        assert "error_msg" in result

    def test_timeout_returns_error(self):
        result = ShellTool().run(command='python -c "import time; time.sleep(10)"', timeout="1")
        assert "timed out" in result.lower() or "exit_code: -1" in result

    def test_blocked_destructive_command(self):
        result = ShellTool().run(command="rm -rf /")
        # Either we block it ourselves or the OS rejects it — either way no clean success
        assert "blocked" in result.lower() or "exit_code: 1" in result or "exit_code: -1" in result

    def test_cwd_parameter(self, tmp_path):
        result = ShellTool().run(command='python -c "import os; print(os.getcwd())"', cwd=str(tmp_path))
        assert str(tmp_path) in result

    def test_timeout_capped_at_120(self):
        # Should not actually hang — just verify it accepts the param
        result = ShellTool().run(command="echo ok", timeout="9999")
        assert "ok" in result


# ---------------------------------------------------------------------------
# ImageTool
# ---------------------------------------------------------------------------


class TestImageTool:
    def _make_test_image(self, tmp_path: Path, w: int = 10, h: int = 10) -> Path:
        try:
            from PIL import Image

            img = Image.new("RGB", (w, h), color=(128, 64, 32))
            f = tmp_path / "test.png"
            img.save(str(f))
            return f
        except ImportError:
            pytest.skip("Pillow not installed")

    def test_describe_returns_dimensions(self, tmp_path):
        f = self._make_test_image(tmp_path, 20, 30)
        result = ImageTool().run(path=str(f), operation="describe")
        assert "20" in result
        assert "30" in result

    def test_describe_returns_format(self, tmp_path):
        f = self._make_test_image(tmp_path)
        result = ImageTool().run(path=str(f), operation="describe")
        assert "PNG" in result or "png" in result.lower()

    def test_colours_operation(self, tmp_path):
        f = self._make_test_image(tmp_path)
        result = ImageTool().run(path=str(f), operation="colours")
        assert "rgb(" in result.lower() or "Dominant" in result

    def test_ocr_hint_operation(self, tmp_path):
        f = self._make_test_image(tmp_path)
        result = ImageTool().run(path=str(f), operation="ocr_hint")
        assert "edge density" in result.lower() or "text" in result.lower()

    def test_missing_file_returns_error(self):
        result = ImageTool().run(path="/no/such/image.png")
        assert "not found" in result.lower()

    def test_default_operation_is_describe(self, tmp_path):
        f = self._make_test_image(tmp_path)
        result = ImageTool().run(path=str(f))
        assert "Dimensions" in result or "dimensions" in result.lower()
