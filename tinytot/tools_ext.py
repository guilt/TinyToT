"""
tinytot.tools_ext — Extended tool library for agentic TinyToT.

Each tool is a concrete subclass of ``Tool``.  New tools are added by subclassing
and appending to ``_REGISTRY``.  The ``ToolRegistry`` singleton exposes them all
via ``get(name)`` and ``all()``.

Tools
-----
WebTool        Fetch a URL, strip HTML, return clean text.
SearchTool     DuckDuckGo lite search → top-N result snippets.
DocumentTool   Extract text from PDF, DOCX, TXT, or Markdown files.
TranslateTool  Translate text via googletrans / Google free endpoint / MyMemory.
DataTool       Explore CSV / JSON / JSONL files — schema, head, describe, query.
FileTool       List, read, search, and stat files on the local filesystem.
ShellTool      Run a shell command and return stdout/stderr (sandboxed timeout).
ImageTool      Describe an image: pixel stats, dominant colours, embedded text via Pillow.
VideoTool      Analyse a video file: duration, FPS, frame count, keyframe snapshots via Pillow.
AudioTool      Analyse an audio file: duration, sample rate, channel count, speech density hint.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import re
import struct
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse

# Optional heavy deps — imported lazily inside each tool to keep startup fast.
# Listed here for documentation; each tool guards its own import with try/except.
#   httpx            — HTTP/HTTPS/SOCKS requests (WebTool, SearchTool, TranslateTool)
#   beautifulsoup4   — HTML stripping (WebTool, SearchTool)
#   pypdf            — PDF text extraction (DocumentTool)
#   python-docx      — DOCX text extraction (DocumentTool)
#   googletrans      — Google Translate wrapper for TranslateTool (pip install tinytot[translation])
#   Pillow           — Image analysis (ImageTool, VideoTool)
#   yt-dlp           — Media download from 1000+ sites (MediaFetchTool)

logger = logging.getLogger(__name__)

__all__ = [
    "Tool",
    "ToolRegistry",
    "WebTool",
    "SearchTool",
    "DocumentTool",
    "TranslateTool",
    "DataTool",
    "FileTool",
    "ShellTool",
    "ImageTool",
    "VideoTool",
    "AudioTool",
    "MediaFetchTool",
    "registry",
]

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
_HTTP_TIMEOUT = 15.0
_SHELL_TIMEOUT = 30

# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class Tool(ABC):
    """Base class for all TinyToT agent tools."""

    name: str
    description: str
    # Parameter schema — list of (name, description, required) tuples
    params: List[Tuple[str, str, bool]] = []

    def schema(self) -> Dict[str, Any]:
        """Return an OpenAI-compatible function-tool schema dict."""
        props: Dict[str, Any] = {}
        required: List[str] = []
        for pname, pdesc, preq in self.params:
            props[pname] = {"type": "string", "description": pdesc}
            if preq:
                required.append(pname)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required,
                },
            },
        }

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        """Execute the tool and return a plain-text result."""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class ToolRegistry:
    """Holds all registered tools and dispatches by name."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def all(self) -> List[Tool]:
        return list(self._tools.values())

    def schemas(self) -> List[Dict[str, Any]]:
        return [t.schema() for t in self._tools.values()]

    def run(self, name: str, **kwargs: Any) -> str:
        tool = self.get(name)
        if tool is None:
            return f"[ToolRegistry] unknown tool: {name!r}"
        try:
            return tool.run(**kwargs)
        except Exception as exc:
            logger.warning("Tool %s raised: %s", name, exc)
            return f"[{name} error] {exc}"


# ---------------------------------------------------------------------------
# WebTool
# ---------------------------------------------------------------------------


class WebTool(Tool):
    """Fetch a URL and return clean readable text (HTML stripped)."""

    name = "web_fetch"
    description = (
        "Fetch the content of a URL and return clean readable text. "
        "Use for web pages, articles, documentation, or any HTTP resource."
    )
    params = [
        ("url", "Full URL to fetch (https://...)", True),
        ("max_chars", "Maximum characters to return (default 4000)", False),
    ]

    def run(self, url: str, max_chars: str = "4000") -> str:
        limit = int(max_chars) if str(max_chars).isdigit() else 4000
        try:
            import httpx
            from bs4 import BeautifulSoup

            headers = {"User-Agent": "TinyToT/0.2 (+https://github.com/tinytot)"}
            with httpx.Client(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                ct = resp.headers.get("content-type", "")
                if "html" in ct:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                        tag.decompose()
                    text = soup.get_text(separator="\n")
                else:
                    text = resp.text
            # Collapse blank lines
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            result = "\n".join(lines)[:limit]
            return result or "(empty response)"
        except ImportError as e:
            return f"[web_fetch] missing dependency: {e}"
        except Exception as e:
            return f"[web_fetch error] {e}"


# ---------------------------------------------------------------------------
# SearchTool
# ---------------------------------------------------------------------------


class SearchTool(Tool):
    """DuckDuckGo lite search — returns top result snippets, no API key needed."""

    name = "web_search"
    description = (
        "Search the web using DuckDuckGo and return top result titles and snippets. "
        "Use to find papers, news, documentation, or any topic before fetching full pages."
    )
    params = [
        ("query", "Search query string", True),
        ("num_results", "Number of results to return (default 5)", False),
    ]

    def run(self, query: str, num_results: str = "5") -> str:
        n = int(num_results) if str(num_results).isdigit() else 5
        try:
            import httpx
            from bs4 import BeautifulSoup

            params = urlencode({"q": query, "kl": "us-en"})
            url = f"https://html.duckduckgo.com/html/?{params}"
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; TinyToT/0.2)",
                "Accept-Language": "en-US,en;q=0.9",
            }
            with httpx.Client(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
                resp = client.post(url, headers=headers)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            for r in soup.select(".result")[:n]:
                title_el = r.select_one(".result__title")
                snippet_el = r.select_one(".result__snippet")
                url_el = r.select_one(".result__url")
                if title_el:
                    title = title_el.get_text(strip=True)
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                    link = url_el.get_text(strip=True) if url_el else ""
                    results.append(f"• {title}\n  {link}\n  {snippet}")
            return "\n\n".join(results) if results else "(no results found)"
        except ImportError as e:
            return f"[web_search] missing dependency: {e}"
        except Exception as e:
            return f"[web_search error] {e}"


# ---------------------------------------------------------------------------
# DocumentTool
# ---------------------------------------------------------------------------


class DocumentTool(Tool):
    """Extract text from PDF, DOCX, TXT, or Markdown files (local path or URL)."""

    name = "document_extract"
    description = (
        "Extract and return the text content of a document. "
        "Supports PDF, DOCX, TXT, and Markdown. Accepts a local file path or a URL."
    )
    params = [
        ("source", "Local file path or URL to the document", True),
        ("max_chars", "Maximum characters to return (default 8000)", False),
        ("pages", "Page range for PDFs e.g. '1-5' or '3' (default: all)", False),
    ]

    def run(self, source: str, max_chars: str = "8000", pages: str = "") -> str:
        limit = int(max_chars) if str(max_chars).isdigit() else 8000
        src = source.strip()

        # Fetch remote documents into a temp file
        if src.startswith("http://") or src.startswith("https://"):
            try:
                import httpx

                with httpx.Client(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
                    resp = client.get(src)
                    resp.raise_for_status()
                suffix = Path(urlparse(src).path).suffix or ".tmp"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
                    tf.write(resp.content)
                    src = tf.name
            except Exception as e:
                return f"[document_extract] fetch error: {e}"

        path = Path(src)
        if not path.exists():
            return f"[document_extract] file not found: {src}"

        ext = path.suffix.lower()
        try:
            if ext == ".pdf":
                return self._extract_pdf(path, limit, pages)
            elif ext in (".docx", ".doc"):
                return self._extract_docx(path, limit)
            elif ext in (".txt", ".md", ".rst", ".csv", ".log", ".py", ".js", ".ts", ".json", ".yaml", ".yml"):
                return self._extract_text(path, limit)
            else:
                return self._extract_text(path, limit)
        except Exception as e:
            return f"[document_extract error] {e}"

    def _extract_pdf(self, path: Path, limit: int, pages: str) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            total = len(reader.pages)
            if pages:
                idxs = self._parse_page_range(pages, total)
            else:
                idxs = list(range(total))
            parts = []
            for i in idxs:
                if i < total:
                    parts.append(reader.pages[i].extract_text() or "")
            text = "\n".join(parts)
            return text[:limit] or "(no text extracted from PDF)"
        except ImportError:
            return "[document_extract] pypdf not installed"

    def _extract_docx(self, path: Path, limit: int) -> str:
        try:
            import docx

            doc = docx.Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs)
            return text[:limit] or "(empty document)"
        except ImportError:
            return "[document_extract] python-docx not installed"

    def _extract_text(self, path: Path, limit: int) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace")[:limit]
        except Exception as e:
            return f"[document_extract text error] {e}"

    @staticmethod
    def _parse_page_range(spec: str, total: int) -> List[int]:
        """Parse '1-5' or '3' into 0-based indices."""
        spec = spec.strip()
        if "-" in spec:
            parts = spec.split("-", 1)
            try:
                start = max(0, int(parts[0].strip()) - 1)
                end = min(total, int(parts[1].strip()))
                return list(range(start, end))
            except ValueError:
                pass
        try:
            return [int(spec) - 1]
        except ValueError:
            return list(range(total))


# ---------------------------------------------------------------------------
# TranslateTool
# ---------------------------------------------------------------------------


class TranslateTool(Tool):
    """Translate text between languages using deep-translator (Google backend, free)."""

    name = "translate"
    description = (
        "Translate text from one language to another. "
        "Uses Google Translate via deep-translator (no API key needed). "
        "Language codes: 'en', 'fr', 'de', 'es', 'zh-CN', 'ja', 'ar', etc. "
        "Set source to 'auto' to detect automatically."
    )
    params = [
        ("text", "Text to translate", True),
        ("target", "Target language code (e.g. 'en', 'fr', 'de')", True),
        ("source", "Source language code or 'auto' (default: auto)", False),
    ]

    def run(self, text: str, target: str = "en", source: str = "auto") -> str:
        """Translate text through a backend fallback chain.

        Backends tried in order:
          1. argostranslate — fully offline Python library, no network after pack install.
             Install packs: python -m argostranslate.package --install en ko
             LibreTranslate uses this same engine internally.
          2. LibreTranslate HTTP (local) — if running at LIBRETRANSLATE_URL (default
             http://localhost:5000). Start with: pip install libretranslate && libretranslate
          3. Google Translate free endpoint via httpx (proxy-aware, HTTP_PROXY/SOCKS).
          4. MyMemory free API via httpx.
          5. Graceful no-op — returns original text with a helpful message.
        """
        if not text or not text.strip():
            return text

        chunks = [text[i : i + 4900] for i in range(0, len(text), 4900)]
        translated_parts = []
        for chunk in chunks:
            result = self._translate_chunk(chunk, source, target)
            if result.startswith("[translate]"):
                return result  # unrecoverable — return error from first chunk
            translated_parts.append(result)
        return " ".join(translated_parts)

    def _translate_chunk(self, text: str, source: str, target: str) -> str:
        src = _norm_lang(source)
        tgt = _norm_lang(target)

        # Backend 1: argostranslate via ctranslate2 — offline, no network after pack install
        result = _ct2_translate(text, src, tgt)
        if result is not None:
            return result

        # Backend 2: LibreTranslate local HTTP server (set LIBRETRANSLATE_URL env var)
        import httpx

        libretranslate_url = os.environ.get("LIBRETRANSLATE_URL", "http://localhost:5000")
        try:
            with httpx.Client(timeout=5.0, trust_env=False) as client:
                resp = client.post(
                    f"{libretranslate_url}/translate",
                    json={"q": text, "source": source, "target": target, "format": "text"},
                )
                resp.raise_for_status()
                return resp.json().get("translatedText", text)
        except Exception:
            pass

        # Backend 3: googletrans — free Google Translate wrapper (if installed)
        try:
            from googletrans import Translator as _Gt

            return _Gt().translate(text, src=src, dest=tgt).text
        except Exception:
            pass

        # Backend 4: Google Translate free endpoint (honours HTTP_PROXY / ALL_PROXY)
        try:
            with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
                resp = client.get(
                    "https://translate.googleapis.com/translate_a/single",
                    params={"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text},
                )
                resp.raise_for_status()
                data = resp.json()
                return "".join(seg[0] for seg in data[0] if seg and seg[0])
        except Exception:
            pass

        # Backend 5: MyMemory free API
        try:
            src_code = source if source != "auto" else "en"
            with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
                resp = client.get(
                    "https://api.mymemory.translated.world/get",
                    params={"q": text[:500], "langpair": f"{src_code}|{target}"},
                )
                resp.raise_for_status()
                translated = resp.json().get("responseData", {}).get("translatedText", "")
                if translated and translated.upper() != text.upper():
                    return translated
        except Exception:
            pass

        return f"[translate] No working backend for {source}→{target}. Run: pipenv run tinytot-ingest translate-packs"


# ---------------------------------------------------------------------------
# Module-level translation helpers (used by TranslateTool._translate_chunk)
# ---------------------------------------------------------------------------


def _norm_lang(code: str) -> str:
    """Normalise a language code: zh-CN → zh, auto → en, etc."""
    if not code or code == "auto":
        return "en"
    return code.lower().split("-")[0]


def _ct2_find_pkg(src: str, tgt: str):
    """Return the installed argostranslate package for src→tgt, or None.

    Skips packages that use the older bpe.model format (not sentencepiece-compatible).
    """
    try:
        from pathlib import Path as _P

        import argostranslate.package

        for p in argostranslate.package.get_installed_packages():
            if p.from_code == src and p.to_code == tgt and p.package_path:
                if (_P(p.package_path) / "sentencepiece.model").exists():
                    return p
    except ImportError:
        pass
    return None


def _ct2_translate_sentence(pkg, sentence: str) -> str:
    """Translate a single sentence using ctranslate2 + sentencepiece/BPE directly."""
    import ctranslate2
    import sentencepiece

    path = Path(pkg.package_path)
    # Prefer sentencepiece.model; bpe.model from older packs may not be sp-compatible
    sp_file = path / "sentencepiece.model" if (path / "sentencepiece.model").exists() else None
    if sp_file is None:
        return sentence  # no usable tokenizer — return original unchanged

    sp = sentencepiece.SentencePieceProcessor()
    sp.Load(str(sp_file))
    model = ctranslate2.Translator(str(path / "model"), device="cpu")
    tokens = sp.EncodeAsPieces(sentence)
    result = model.translate_batch([tokens])
    decoded = sp.DecodePieces(result[0].hypotheses[0])
    return decoded.replace("▁", " ").strip()


def _ct2_translate(text: str, src: str, tgt: str) -> str | None:
    """Translate text offline via ctranslate2, with English pivot for unsupported pairs.

    Returns the translated string, or None if no pack is available.
    """
    try:
        import ctranslate2  # noqa: F401 — just to check availability
        import sentencepiece  # noqa: F401
    except ImportError:
        return None

    def _translate_with_pkg(pkg, content: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", content.strip()) or [content]
        return " ".join(_ct2_translate_sentence(pkg, s) for s in sentences if s)

    # Direct translation
    pkg = _ct2_find_pkg(src, tgt)
    if pkg:
        return _translate_with_pkg(pkg, text)

    # Pivot via English: src→en then en→tgt
    if src != "en" and tgt != "en":
        src_en = _ct2_find_pkg(src, "en")
        en_tgt = _ct2_find_pkg("en", tgt)
        if src_en and en_tgt:
            mid = _translate_with_pkg(src_en, text)
            return _translate_with_pkg(en_tgt, mid)

    # Pack not installed — try to download it once
    try:
        import argostranslate.package

        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        pkg = next((p for p in available if p.from_code == src and p.to_code == tgt), None)
        if pkg:
            argostranslate.package.install_from_path(pkg.download())
            new_pkg = _ct2_find_pkg(src, tgt)
            if new_pkg:
                return _translate_with_pkg(new_pkg, text)
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# DataTool
# ---------------------------------------------------------------------------


class DataTool(Tool):
    """Explore structured data files: CSV, JSON, JSONL, and Parquet."""

    name = "data_explore"
    description = (
        "Explore a structured data file (CSV, JSON, JSONL). "
        "Operations: 'schema' (column types), 'head' (first N rows), "
        "'describe' (basic stats), 'query' (filter rows by a column=value expression)."
    )
    params = [
        ("path", "Local path to the data file", True),
        ("operation", "One of: schema, head, describe, query (default: head)", False),
        ("arg", "Extra argument: N for head, or col=val for query", False),
    ]

    def run(self, path: str, operation: str = "head", arg: str = "") -> str:
        p = Path(path)
        if not p.exists():
            return f"[data_explore] file not found: {path}"
        ext = p.suffix.lower()
        try:
            if ext == ".csv":
                return self._handle_csv(p, operation, arg)
            elif ext in (".json",):
                return self._handle_json(p, operation, arg)
            elif ext == ".jsonl":
                return self._handle_jsonl(p, operation, arg)
            else:
                return f"[data_explore] unsupported format: {ext}"
        except Exception as e:
            return f"[data_explore error] {e}"

    def _handle_csv(self, path: Path, operation: str, arg: str) -> str:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            return "(empty CSV)"
        cols = list(rows[0].keys())
        if operation == "schema":
            return "Columns: " + ", ".join(cols) + f"\nRows: {len(rows)}"
        if operation == "head":
            n = int(arg) if arg.isdigit() else 5
            return self._rows_to_text(cols, rows[:n])
        if operation == "describe":
            return self._describe(cols, rows)
        if operation == "query":
            return self._query(cols, rows, arg)
        return self._rows_to_text(cols, rows[:5])

    def _handle_json(self, path: Path, operation: str, arg: str) -> str:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            rows = [r if isinstance(r, dict) else {"value": r} for r in data]
            cols = list(rows[0].keys()) if rows else []
            if operation == "schema":
                return f"Array of {len(rows)} objects. Keys: {', '.join(cols)}"
            if operation == "head":
                n = int(arg) if arg.isdigit() else 5
                return self._rows_to_text(cols, rows[:n])
            if operation == "describe":
                return self._describe(cols, rows)
            if operation == "query":
                return self._query(cols, rows, arg)
        return json.dumps(data, indent=2)[:4000]

    def _handle_jsonl(self, path: Path, operation: str, arg: str) -> str:
        rows = []
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        if not rows:
            return "(empty JSONL)"
        cols = list(rows[0].keys()) if isinstance(rows[0], dict) else ["value"]
        if operation == "schema":
            return f"JSONL: {len(rows)} records. Keys: {', '.join(cols)}"
        if operation == "head":
            n = int(arg) if arg.isdigit() else 5
            return self._rows_to_text(cols, rows[:n])
        if operation == "describe":
            return self._describe(cols, rows)
        if operation == "query":
            return self._query(cols, rows, arg)
        return self._rows_to_text(cols, rows[:5])

    @staticmethod
    def _rows_to_text(cols: List[str], rows: List[dict]) -> str:
        lines = [" | ".join(cols)]
        lines.append("-" * len(lines[0]))
        for row in rows:
            lines.append(" | ".join(str(row.get(c, ""))[:40] for c in cols))
        return "\n".join(lines)

    @staticmethod
    def _describe(cols: List[str], rows: List[dict]) -> str:
        lines = [f"Rows: {len(rows)}", f"Columns: {len(cols)}"]
        for col in cols[:20]:
            vals = [row.get(col, "") for row in rows]
            non_empty = [v for v in vals if v not in ("", None)]
            nums = []
            for v in non_empty:
                try:
                    nums.append(float(v))
                except (TypeError, ValueError):
                    pass
            if nums:
                lines.append(
                    f"  {col}: min={min(nums):.2g} max={max(nums):.2g} mean={sum(nums) / len(nums):.2g} (n={len(nums)})"
                )
            else:
                uniq = len(set(str(v) for v in non_empty))
                lines.append(f"  {col}: {uniq} unique values, {len(non_empty)} non-empty")
        return "\n".join(lines)

    @staticmethod
    def _query(cols: List[str], rows: List[dict], arg: str) -> str:
        # Supports: col=val, col!=val, col>val, col<val
        m = re.match(r"(\w+)\s*(!=|>=|<=|>|<|=)\s*(.+)", arg.strip())
        if not m:
            return f"[data_explore] query format: col=value (got: {arg!r})"
        col, op, val = m.group(1), m.group(2), m.group(3).strip()
        results = []
        for row in rows:
            cell = str(row.get(col, ""))
            try:
                nc, nv = float(cell), float(val)
                match = (
                    (op in ("=", "==") and nc == nv)
                    or (op == "!=" and nc != nv)
                    or (op == ">" and nc > nv)
                    or (op == "<" and nc < nv)
                    or (op == ">=" and nc >= nv)
                    or (op == "<=" and nc <= nv)
                )
            except ValueError:
                match = (op in ("=", "==") and cell == val) or (op == "!=" and cell != val)
            if match:
                results.append(row)
        if not results:
            return f"(no rows matched {arg})"
        return DataTool._rows_to_text(cols, results[:20])


# ---------------------------------------------------------------------------
# FileTool
# ---------------------------------------------------------------------------


class FileTool(Tool):
    """Explore the local filesystem: list, read, search, stat."""

    name = "file_explore"
    description = (
        "Explore the local filesystem. "
        "Operations: 'list' (directory listing), 'read' (file contents), "
        "'search' (grep for text in files), 'stat' (file metadata), "
        "'find' (find files by name pattern)."
    )
    params = [
        ("path", "Local path — directory or file", True),
        ("operation", "One of: list, read, search, stat, find (default: list)", False),
        ("arg", "Extra arg: search query, glob pattern for find, or line range N-M for read", False),
        ("max_chars", "Max characters for read output (default 6000)", False),
    ]

    # Paths that should never be read
    _DENY = re.compile(
        r"(\.env|\.netrc|\.ssh|id_rsa|id_dsa|id_ecdsa|id_ed25519|\.pypirc|\.aws|\.azure|\.gcp)",
        re.IGNORECASE,
    )

    def run(self, path: str, operation: str = "list", arg: str = "", max_chars: str = "6000") -> str:
        limit = int(max_chars) if str(max_chars).isdigit() else 6000
        p = Path(path).expanduser()
        op = operation.lower().strip()
        if op == "list":
            return self._list(p)
        if op == "read":
            return self._read(p, arg, limit)
        if op == "search":
            return self._search(p, arg, limit)
        if op == "stat":
            return self._stat(p)
        if op == "find":
            return self._find(p, arg)
        return self._list(p)

    def _list(self, p: Path) -> str:
        if not p.exists():
            return f"[file_explore] path not found: {p}"
        if p.is_file():
            return self._stat(p)
        entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
        lines = []
        for e in entries[:200]:
            kind = "DIR " if e.is_dir() else "FILE"
            size = f"{e.stat().st_size:>10,}B" if e.is_file() else "          "
            lines.append(f"{kind}  {size}  {e.name}")
        if len(list(p.iterdir())) > 200:
            lines.append(f"... (truncated, {len(list(p.iterdir()))} total entries)")
        return "\n".join(lines) if lines else "(empty directory)"

    def _read(self, p: Path, arg: str, limit: int) -> str:
        if self._DENY.search(str(p)):
            return "[file_explore] reading this file is not permitted"
        if not p.exists():
            return f"[file_explore] file not found: {p}"
        if not p.is_file():
            return f"[file_explore] not a file: {p}"
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"[file_explore read error] {e}"
        # Optional line range: "10-50"
        if "-" in arg:
            parts = arg.split("-", 1)
            try:
                start, end = int(parts[0]) - 1, int(parts[1])
                lines = text.splitlines()
                text = "\n".join(lines[start:end])
            except ValueError:
                pass
        return text[:limit]

    def _search(self, p: Path, query: str, limit: int) -> str:
        if not query:
            return "[file_explore] search requires a query arg"
        p = p if p.exists() else Path(".")
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        results = []
        target = [p] if p.is_file() else sorted(p.rglob("*"))
        for f in target:
            if not f.is_file():
                continue
            if self._DENY.search(str(f)):
                continue
            try:
                for i, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
                    if pattern.search(line):
                        results.append(f"{f}:{i}: {line.strip()[:120]}")
                        if len(results) >= 50:
                            break
            except Exception:
                pass
            if len(results) >= 50:
                break
        return "\n".join(results[: limit // 80]) if results else f"(no matches for {query!r})"

    @staticmethod
    def _stat(p: Path) -> str:
        if not p.exists():
            return f"[file_explore] not found: {p}"
        s = p.stat()
        import datetime

        mtime = datetime.datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        kind = "directory" if p.is_dir() else "file"
        return (
            f"Path:     {p.resolve()}\n"
            f"Type:     {kind}\n"
            f"Size:     {s.st_size:,} bytes\n"
            f"Modified: {mtime}\n"
            f"Mode:     {oct(s.st_mode)}"
        )

    @staticmethod
    def _find(p: Path, pattern: str) -> str:
        if not pattern:
            pattern = "*"
        base = p if p.exists() else Path(".")
        matches = sorted(base.rglob(pattern))[:100]
        if not matches:
            return f"(no files matching {pattern!r} under {base})"
        return "\n".join(str(m) for m in matches)


# ---------------------------------------------------------------------------
# ShellTool
# ---------------------------------------------------------------------------


class ShellTool(Tool):
    """Run a shell command and return stdout + stderr."""

    name = "shell_run"
    description = (
        "Run a shell command and return its output (stdout + stderr). "
        "Use for git, build tools, data processing scripts, or any CLI operation. "
        "Commands run with a 30s timeout."
    )
    params = [
        ("command", "Shell command to run", True),
        ("cwd", "Working directory (default: current)", False),
        ("timeout", "Timeout in seconds (default: 30)", False),
    ]

    _BLOCKED = re.compile(
        r"\b(rm\s+-rf\s+/|dd\s+if=|mkfs|fdisk|:(){ :|:& };:)\b",
        re.IGNORECASE,
    )

    def run(self, command: str, cwd: str = "", timeout: str = "30") -> str:
        if self._BLOCKED.search(command):
            return "[shell_run] command blocked for safety"
        secs = int(timeout) if str(timeout).isdigit() else _SHELL_TIMEOUT
        secs = min(secs, 120)
        work_dir = cwd.strip() or None
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=secs,
                cwd=work_dir,
                env=os.environ.copy(),
            )
            stdout = result.stdout.strip() or "(empty)"
            stderr = result.stderr.strip() or "(empty)"
            return f"exit_code: {result.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}"
        except subprocess.TimeoutExpired:
            return f"exit_code: -1\nstdout: (empty)\nstderr: timed out after {secs}s"
        except Exception as e:
            return f"exit_code: -1\nstdout: (empty)\nstderr: {e}"


# ---------------------------------------------------------------------------
# ImageTool
# ---------------------------------------------------------------------------


def _img_pixels(img):
    """Return pixel data as a list, compatible with Pillow 10–14+."""
    try:
        return list(img.get_flattened_data())
    except AttributeError:
        return list(img.getdata())


class ImageTool(Tool):
    """Analyse an image file: dimensions, colour palette, pixel stats, and embedded text.

    This is TinyToT's deterministic first pass — no neural weights required.
    It uses Pillow for pixel analysis and a simple frequency-based OCR heuristic
    to surface large text regions.  For full vision / OCR, wire an external model.
    """

    name = "image_analyse"
    description = (
        "Analyse a local image file. Returns dimensions, colour mode, dominant colours, "
        "brightness stats, and any large text regions detected via simple OCR heuristics. "
        "Accepts JPEG, PNG, BMP, GIF, TIFF, WebP."
    )
    params = [
        ("path", "Local path to the image file", True),
        ("operation", "One of: describe (default), colours, ocr_hint", False),
    ]

    def run(self, path: str, operation: str = "describe") -> str:
        p = Path(path).expanduser()
        if not p.exists():
            return f"[image_analyse] file not found: {path}"
        try:
            from PIL import Image

            img = Image.open(str(p))
            op = operation.lower().strip()
            if op == "colours":
                return self._dominant_colours(img)
            if op == "ocr_hint":
                return self._ocr_hint(img)
            return self._describe(img, p)
        except ImportError:
            return "[image_analyse] Pillow not installed"
        except Exception as e:
            return f"[image_analyse error] {e}"

    @staticmethod
    def _describe(img: Any, p: Path) -> str:
        from PIL import ImageStat

        size_bytes = p.stat().st_size
        w, h = img.size
        mode = img.mode
        stat = ImageStat.Stat(img.convert("RGB"))
        brightness = sum(stat.mean) / 3
        lines = [
            f"File:        {p.name}",
            f"Size:        {size_bytes:,} bytes",
            f"Dimensions:  {w} × {h} px",
            f"Mode:        {mode}",
            f"Brightness:  {brightness:.1f}/255",
            f"Format:      {img.format or 'unknown'}",
        ]
        # Dominant colour
        try:
            small = img.convert("RGB").resize((50, 50))
            pixels = _img_pixels(small)

            r_avg = sum(px[0] for px in pixels) // len(pixels)
            g_avg = sum(px[1] for px in pixels) // len(pixels)
            b_avg = sum(px[2] for px in pixels) // len(pixels)
            lines.append(f"Avg colour:  rgb({r_avg}, {g_avg}, {b_avg})  #{r_avg:02x}{g_avg:02x}{b_avg:02x}")
        except Exception:
            pass
        return "\n".join(lines)

    @staticmethod
    def _dominant_colours(img: Any, n: int = 8) -> str:
        """Return the N most common colours in the image (quantized to 32 levels)."""
        from collections import Counter

        small = img.convert("RGB").resize((100, 100))
        quantized = [(r >> 3 << 3, g >> 3 << 3, b >> 3 << 3) for r, g, b in _img_pixels(small)]
        counts = Counter(quantized).most_common(n)
        lines = ["Dominant colours (rgb / hex):"]
        for (r, g, b), cnt in counts:
            lines.append(f"  rgb({r:3d},{g:3d},{b:3d})  #{r:02x}{g:02x}{b:02x}  ({cnt} px)")
        return "\n".join(lines)

    @staticmethod
    def _ocr_hint(img: Any) -> str:
        """Very basic OCR hint: finds high-contrast rectangular regions likely containing text."""
        try:
            from PIL import ImageFilter

            gray = img.convert("L").filter(ImageFilter.FIND_EDGES)
            w, h = gray.size
            pixels = _img_pixels(gray)
            bright = sum(1 for p in pixels if p > 128)
            ratio = bright / len(pixels) if pixels else 0
            if ratio > 0.15:
                return (
                    f"High edge density ({ratio:.1%}) — image likely contains text or fine detail.\n"
                    "Consider using an external OCR tool (tesseract, easyocr) for full extraction."
                )
            return (
                f"Low edge density ({ratio:.1%}) — image appears to be a photo or illustration "
                "with little embedded text."
            )
        except Exception as e:
            return f"[ocr_hint error] {e}"


# ---------------------------------------------------------------------------
# VideoTool
# ---------------------------------------------------------------------------


class VideoTool(Tool):
    """Analyse a video file: duration, FPS, frame count, and keyframe snapshots.

    Uses only the Python standard library + Pillow — no ffmpeg required.
    Supports GIF (via Pillow) and raw AVI/MP4 header parsing for metadata.
    For full frame extraction from MP4/AVI, installs gracefully with ffmpeg
    available via ShellTool; otherwise returns header-level metadata only.
    """

    name = "video_analyse"
    description = (
        "Analyse a local video or animated GIF file. Returns duration, frame count, "
        "dimensions, and colour snapshots of keyframes. "
        "Accepts GIF, MP4, AVI, MOV, WebM. For MP4/AVI, uses ffprobe when available."
    )
    params = [
        ("path", "Local path to the video or GIF file", True),
        ("operation", "One of: describe (default), frames, keyframe", False),
        ("frame_num", "Frame number to extract for keyframe operation (default: 0)", False),
    ]

    def run(self, path: str, operation: str = "describe", frame_num: str = "0") -> str:
        p = Path(path).expanduser()
        if not p.exists():
            return f"[video_analyse] file not found: {path}"
        ext = p.suffix.lower()
        op = operation.lower().strip()
        try:
            if ext == ".gif":
                return self._analyse_gif(p, op, int(frame_num) if frame_num.isdigit() else 0)
            else:
                return self._analyse_video(p, op, int(frame_num) if frame_num.isdigit() else 0)
        except Exception as e:
            return f"[video_analyse error] {e}"

    def _analyse_gif(self, p: Path, op: str, frame_num: int) -> str:
        from PIL import Image

        img = Image.open(str(p))
        frames = []
        try:
            while True:
                frames.append(img.copy())
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        w, h = frames[0].size if frames else (0, 0)
        duration_ms = sum(f.info.get("duration", 100) for f in frames)
        fps_approx = len(frames) / (duration_ms / 1000) if duration_ms else 0
        size_bytes = p.stat().st_size

        if op == "frames":
            lines = [f"GIF: {len(frames)} frames  {w}×{h}  {duration_ms}ms  ~{fps_approx:.1f}fps"]
            for i, f in enumerate(frames[:8]):
                lines.append(f"  Frame {i}: duration={f.info.get('duration', 100)}ms")
            if len(frames) > 8:
                lines.append(f"  ... ({len(frames) - 8} more frames)")
            return "\n".join(lines)

        if op == "keyframe":
            if frame_num >= len(frames):
                return f"[video_analyse] frame {frame_num} out of range (total {len(frames)})"
            frame = frames[frame_num].convert("RGB")
            from tinytot.tools_ext import _img_pixels

            pixels = _img_pixels(frame.resize((50, 50)))
            r_avg = sum(px[0] for px in pixels) // len(pixels)
            g_avg = sum(px[1] for px in pixels) // len(pixels)
            b_avg = sum(px[2] for px in pixels) // len(pixels)
            return (
                f"Frame {frame_num}: {frame.size[0]}×{frame.size[1]}  "
                f"avg colour rgb({r_avg},{g_avg},{b_avg}) #{r_avg:02x}{g_avg:02x}{b_avg:02x}"
            )

        # describe (default)
        return (
            f"File:       {p.name}\n"
            f"Format:     GIF\n"
            f"Size:       {size_bytes:,} bytes\n"
            f"Dimensions: {w}×{h} px\n"
            f"Frames:     {len(frames)}\n"
            f"Duration:   {duration_ms}ms  (~{fps_approx:.1f} fps)\n"
        )

    def _analyse_video(self, p: Path, op: str, frame_num: int) -> str:
        size_bytes = p.stat().st_size
        ext = p.suffix.lower()

        # Try ffprobe first for rich metadata
        try:
            import subprocess as _sp

            result = _sp.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", str(p)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                import json as _json

                data = _json.loads(result.stdout)
                fmt = data.get("format", {})
                duration = float(fmt.get("duration", 0))
                streams = data.get("streams", [])
                video = next((s for s in streams if s.get("codec_type") == "video"), {})
                audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
                w = video.get("width", "?")
                h = video.get("height", "?")
                fps_str = video.get("r_frame_rate", "0/1")
                try:
                    num, den = fps_str.split("/")
                    fps = round(int(num) / int(den), 2)
                except Exception:
                    fps = "?"
                nb_frames = video.get("nb_frames", "?")
                codec = video.get("codec_name", "?")
                audio_codec = audio.get("codec_name", "none")
                channels = audio.get("channels", 0)
                sample_rate = audio.get("sample_rate", "?")

                if op == "keyframe":
                    # Extract frame via ffmpeg
                    t = _sp.run(
                        [
                            "ffmpeg",
                            "-ss",
                            str(frame_num / max(fps if isinstance(fps, float) else 25, 1)),
                            "-i",
                            str(p),
                            "-vframes",
                            "1",
                            "-f",
                            "image2pipe",
                            "-vcodec",
                            "png",
                            "-",
                        ],
                        capture_output=True,
                        timeout=15,
                    )
                    if t.returncode == 0 and t.stdout:
                        import io

                        from PIL import Image

                        img = Image.open(io.BytesIO(t.stdout)).convert("RGB")
                        pixels = _img_pixels(img.resize((50, 50)))
                        r_avg = sum(px[0] for px in pixels) // len(pixels)
                        g_avg = sum(px[1] for px in pixels) // len(pixels)
                        b_avg = sum(px[2] for px in pixels) // len(pixels)
                        return (
                            f"Frame ~{frame_num}: {img.size[0]}×{img.size[1]}  "
                            f"avg colour rgb({r_avg},{g_avg},{b_avg}) #{r_avg:02x}{g_avg:02x}{b_avg:02x}"
                        )

                return (
                    f"File:        {p.name}\n"
                    f"Format:      {ext[1:].upper()}  ({codec})\n"
                    f"Size:        {size_bytes:,} bytes\n"
                    f"Dimensions:  {w}×{h} px\n"
                    f"Duration:    {duration:.2f}s\n"
                    f"FPS:         {fps}\n"
                    f"Frames:      {nb_frames}\n"
                    f"Audio:       {audio_codec}  {channels}ch  {sample_rate}Hz\n"
                )
        except (FileNotFoundError, Exception):
            pass

        # Fallback: header-only metadata from file size
        return (
            f"File:    {p.name}\n"
            f"Format:  {ext[1:].upper()}\n"
            f"Size:    {size_bytes:,} bytes\n"
            f"Note:    Install ffprobe for full metadata (duration, FPS, frame count)\n"
        )


# ---------------------------------------------------------------------------
# AudioTool
# ---------------------------------------------------------------------------


class AudioTool(Tool):
    """Analyse an audio file: duration, sample rate, channels, and speech density hint.

    Uses Python's built-in ``wave`` module for WAV files (no deps).
    For MP3/AAC/OGG, uses ffprobe when available; otherwise returns file-level metadata.
    Speech density is estimated via zero-crossing rate on the raw PCM samples —
    a high ZCR suggests speech or noisy audio; low ZCR suggests music or silence.
    """

    name = "audio_analyse"
    description = (
        "Analyse a local audio file. Returns duration, sample rate, channel count, "
        "bit depth, and a speech density hint based on zero-crossing rate. "
        "Accepts WAV (native), MP3/AAC/OGG/FLAC (requires ffprobe). "
        "For speech transcription, wire an external ASR model."
    )
    params = [
        ("path", "Local path to the audio file", True),
        ("operation", "One of: describe (default), waveform, speech_hint", False),
    ]

    def run(self, path: str, operation: str = "describe") -> str:
        p = Path(path).expanduser()
        if not p.exists():
            return f"[audio_analyse] file not found: {path}"
        ext = p.suffix.lower()
        op = operation.lower().strip()
        try:
            if ext == ".wav":
                return self._analyse_wav(p, op)
            else:
                return self._analyse_ffprobe(p, op)
        except Exception as e:
            return f"[audio_analyse error] {e}"

    def _analyse_wav(self, p: Path, op: str) -> str:
        import wave

        with wave.open(str(p), "rb") as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()  # bytes
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = n_frames / framerate if framerate else 0

            if op in ("waveform", "speech_hint"):
                # Read up to 2s of audio for ZCR analysis
                max_frames = min(n_frames, framerate * 2)
                raw = wf.readframes(max_frames)

            size_bytes = p.stat().st_size
            bit_depth = sample_width * 8

        if op == "waveform":
            # Compute amplitude envelope (RMS per 100ms chunk)
            chunk = framerate // 10
            lines = [f"WAV waveform ({channels}ch  {framerate}Hz  {bit_depth}bit):"]
            for i in range(0, len(raw), sample_width * chunk):
                chunk_bytes = raw[i : i + sample_width * chunk]
                try:
                    samples = list(
                        struct.unpack(
                            f"<{len(chunk_bytes) // sample_width}{'h' if sample_width == 2 else 'b'}", chunk_bytes
                        )
                    )
                    rms = int((sum(s * s for s in samples) / len(samples)) ** 0.5) if samples else 0
                    bar = "#" * (rms * 20 // 32768)
                    lines.append(f"  {bar or '.'}")
                except struct.error:
                    break
                if len(lines) > 25:
                    break
            return "\n".join(lines)

        if op == "speech_hint":
            # Zero-crossing rate as a speech presence proxy
            try:
                fmt_char = "h" if sample_width == 2 else "b"
                samples = list(struct.unpack(f"<{len(raw) // sample_width}{fmt_char}", raw))
                zcr = sum(1 for i in range(1, len(samples)) if samples[i - 1] * samples[i] < 0)
                zcr_rate = zcr / len(samples) if samples else 0
                if zcr_rate > 0.15:
                    hint = "High ZCR — likely speech or noisy audio"
                elif zcr_rate > 0.05:
                    hint = "Moderate ZCR — may contain speech or complex audio"
                else:
                    hint = "Low ZCR — likely music, tones, or silence"
                return (
                    f"Speech density hint for {p.name}:\n"
                    f"  Zero-crossing rate: {zcr_rate:.3f}\n"
                    f"  Assessment: {hint}\n"
                    f"  Note: For accurate transcription, wire an ASR model (Whisper, etc.)\n"
                )
            except Exception as e:
                return f"[audio_analyse speech_hint error] {e}"

        # describe
        return (
            f"File:         {p.name}\n"
            f"Format:       WAV\n"
            f"Size:         {size_bytes:,} bytes\n"
            f"Duration:     {duration:.2f}s\n"
            f"Sample rate:  {framerate} Hz\n"
            f"Channels:     {channels}\n"
            f"Bit depth:    {bit_depth}-bit\n"
            f"Frames:       {n_frames:,}\n"
        )

    def _analyse_ffprobe(self, p: Path, op: str) -> str:
        size_bytes = p.stat().st_size
        ext = p.suffix.lower()
        try:
            import json as _json
            import subprocess as _sp

            result = _sp.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(p)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                data = _json.loads(result.stdout)
                streams = data.get("streams", [])
                audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
                duration = float(audio.get("duration", 0))
                codec = audio.get("codec_name", "?")
                channels = audio.get("channels", "?")
                sample_rate = audio.get("sample_rate", "?")
                bit_rate = audio.get("bit_rate", "?")
                return (
                    f"File:         {p.name}\n"
                    f"Format:       {ext[1:].upper()}  ({codec})\n"
                    f"Size:         {size_bytes:,} bytes\n"
                    f"Duration:     {duration:.2f}s\n"
                    f"Sample rate:  {sample_rate} Hz\n"
                    f"Channels:     {channels}\n"
                    f"Bit rate:     {bit_rate} bps\n"
                    f"Note:         For speech transcription, wire Whisper or another ASR model.\n"
                )
        except (FileNotFoundError, Exception):
            pass

        return (
            f"File:   {p.name}\n"
            f"Format: {ext[1:].upper()}\n"
            f"Size:   {size_bytes:,} bytes\n"
            f"Note:   Install ffprobe for full audio metadata. For WAV files no extra deps needed.\n"
        )


# ---------------------------------------------------------------------------
# MediaFetchTool  (yt-dlp wrapper)
# ---------------------------------------------------------------------------


class MediaFetchTool(Tool):
    """Download and preview media from URLs: YouTube, Twitter/X, Instagram, TikTok, etc.

    Uses yt-dlp for downloading.  By default fetches metadata only (no download)
    so the tool is safe to call on any URL.  Set operation='download' to save
    the media locally and return the file path for further analysis.

    Requires yt-dlp: pip install yt-dlp
    """

    name = "media_fetch"
    description = (
        "Fetch media metadata or download media from a URL (YouTube, Twitter/X, "
        "Instagram, TikTok, Reddit, Vimeo, and thousands more via yt-dlp). "
        "Operations: 'info' (metadata only, default), 'download' (save to disk), "
        "'thumbnail' (download thumbnail image only)."
    )
    params = [
        ("url", "URL of the media to fetch", True),
        ("operation", "One of: info (default), download, thumbnail", False),
        ("output_dir", "Directory to save downloads (default: data/.sources/media/)", False),
    ]

    _DEFAULT_OUT = Path(__file__).parent / "_data" / ".sources" / "media"

    def run(self, url: str, operation: str = "info", output_dir: str = "") -> str:
        op = operation.lower().strip()
        out_dir = Path(output_dir) if output_dir else self._DEFAULT_OUT
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            import yt_dlp
        except ImportError:
            return "[media_fetch] yt-dlp not installed. Run: pip install yt-dlp"

        if op == "info":
            return self._get_info(url, yt_dlp)
        elif op == "thumbnail":
            return self._get_thumbnail(url, out_dir, yt_dlp)
        elif op == "download":
            return self._download(url, out_dir, yt_dlp)
        else:
            return self._get_info(url, yt_dlp)

    def _get_info(self, url: str, yt_dlp) -> str:
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                return f"[media_fetch] no info returned for {url}"
            lines = [
                f"Title:       {info.get('title', 'unknown')}",
                f"Uploader:    {info.get('uploader', 'unknown')}",
                f"Duration:    {info.get('duration', 0)}s",
                f"View count:  {info.get('view_count', 'unknown'):,}"
                if isinstance(info.get("view_count"), int)
                else f"View count:  {info.get('view_count', 'unknown')}",
                f"Upload date: {info.get('upload_date', 'unknown')}",
                f"Description: {str(info.get('description', ''))[:200]}",
                f"Webpage:     {info.get('webpage_url', url)}",
            ]
            tags = info.get("tags", [])
            if tags:
                lines.append(f"Tags:        {', '.join(str(t) for t in tags[:10])}")
            return "\n".join(lines)
        except Exception as e:
            return f"[media_fetch info error] {e}"

    def _get_thumbnail(self, url: str, out_dir: Path, yt_dlp) -> str:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writethumbnail": True,
            "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            title = info.get("title", "unknown") if info else "unknown"
            thumb_url = info.get("thumbnail", "") if info else ""
            # Find downloaded thumbnail
            candidates = list(out_dir.glob(f"{info.get('id', '*')}.*")) if info else []
            img_files = [f for f in candidates if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
            if img_files:
                result = ImageTool().run(path=str(img_files[0]))
                return f"Thumbnail for: {title}\nFile: {img_files[0]}\n{result}"
            return f"Thumbnail URL: {thumb_url}\nTitle: {title}"
        except Exception as e:
            return f"[media_fetch thumbnail error] {e}"

    def _download(self, url: str, out_dir: Path, yt_dlp) -> str:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
            "format": "best[height<=720]/best",  # cap at 720p
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            title = info.get("title", "unknown") if info else "unknown"
            # Find the downloaded file
            candidates = sorted(out_dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
            downloaded = candidates[0] if candidates else None
            if downloaded:
                size = downloaded.stat().st_size
                return (
                    f"Downloaded: {title}\n"
                    f"File:       {downloaded}\n"
                    f"Size:       {size:,} bytes\n"
                    f"Tip: Use video_analyse or audio_analyse for further inspection."
                )
            return f"Download completed for: {title}"
        except Exception as e:
            return f"[media_fetch download error] {e}"


# ---------------------------------------------------------------------------
# Global registry singleton
# ---------------------------------------------------------------------------

registry = ToolRegistry()
for _tool_cls in [
    WebTool,
    SearchTool,
    DocumentTool,
    TranslateTool,
    DataTool,
    FileTool,
    ShellTool,
    ImageTool,
    VideoTool,
    AudioTool,
    MediaFetchTool,
]:
    registry.register(_tool_cls())
