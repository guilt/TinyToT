"""
tinytot.agent — Agentic Plan-Execute loop for TinyToT.

Architecture
------------
The agent sits between ``generateReasoningResponse()`` and the tool layer.
When a prompt needs more than static knowledge retrieval, the agent:

  1. **Plans** — uses ToT to decompose the prompt into a sequence of steps,
     each tagged with a tool name and parameters.
  2. **Executes** — runs each step via the ``ToolRegistry``, accumulating
     context from tool outputs.
  3. **Synthesises** — feeds the accumulated context back into ToT to produce
     a final grounded response.

Learning journal (Hermes-compatible)
-------------------------------------
Every agent run can optionally record observations to a markdown journal at
``data/journal/YYYY-MM-DD.md``.  The format mirrors Hermes so that Hermes can
read TinyToT's journal as a knowledge source and vice-versa.  Learnings are
automatically reloaded into TinyToT's knowledge index at the start of each server
process (``loadHermesJournal`` in ``content.py`` already handles parsing).

Agent needs detection
---------------------
``detectAgentNeeds(prompt)`` is a fast heuristic that returns True when the
prompt requires capabilities beyond the static knowledge base:
  - URL or file path present
  - research / paper / translate / analyse keywords
  - multi-step questions ("first … then …", "step by step")
  - explicit tool invocation ("search for", "read the file", "run")
"""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .content import DATA_DIR as _DATA_DIR
from .lang import LANG_NAMES_PATTERN, Lang, detect_lang

logger = logging.getLogger(__name__)

__all__ = [
    "detectAgentNeeds",
    "agentResponse",
    "LearningJournal",
    "PlanExecuteLoop",
]

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_JOURNAL_DIR = _DATA_DIR / "journal"

# ---------------------------------------------------------------------------
# Agent-need detection patterns
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_FILE_PATH_RE = re.compile(r"(?:^|[\s'\"])(/[\w./\-]+|~/[\w./\-]+|\.{1,2}/[\w./\-]+)", re.IGNORECASE)

_AGENT_KEYWORDS = re.compile(
    r"\b("
    r"search(\s+for)?|look(\s+up)?|find(\s+me)?|fetch|download|scrape"
    r"|read(\s+the)?\s+(file|document|pdf|paper|article|page|url)"
    r"|translate|translation"
    r"|answer\s+in\s+(?:" + LANG_NAMES_PATTERN + r")"
    r"|respond\s+in\s+\w+|reply\s+in\s+\w+"
    r"|in\s+(?:" + LANG_NAMES_PATTERN + r")"
    r"|analyse|analyze|explore(\s+the)?(\s+data)?"
    r"|summarize(\s+the)?\s+(paper|article|document|page|url)"
    r"|research|investigate|study"
    r"|run(\s+the)?(\s+command)?|execute|shell"
    r"|what('s|\s+is)\s+in(\s+the)?\s+(file|directory|folder|image)"
    r"|list(\s+the)?(\s+files)?"
    r"|open(\s+the)?\s+(image|file|picture|photo|video)"
    r"|who\s+wrote|who\s+published|cite\s+"
    r"|what\s+(day|time|date)\s+is\s+it|what.s\s+today|today.s\s+date"
    r")\b",
    re.IGNORECASE,
)

_MULTI_STEP_RE = re.compile(
    r"\b(first\b.{0,60}\bthen\b|step\s+by\s+step|then\s+summarize|and\s+then|after\s+that)\b",
    re.IGNORECASE,
)

# Non-ASCII (CJK, Arabic, Devanagari, Hangul, etc.) — any non-Latin script triggers translate tool
_NON_ASCII_RE = re.compile(r"[؀-ۿऀ-ॿ　-鿿가-힯一-鿿぀-ヿ]")

# Explicit tool invocation patterns
_TOOL_TRIGGER_RE = re.compile(
    r"\b(google|bing|duckduckgo|ddg|arxiv|wikipedia|github)\b",
    re.IGNORECASE,
)


def detectAgentNeeds(prompt: str) -> bool:
    """Return True if the prompt requires the agent loop."""
    if _URL_RE.search(prompt):
        return True
    if _FILE_PATH_RE.search(prompt):
        return True
    if _AGENT_KEYWORDS.search(prompt):
        return True
    if _MULTI_STEP_RE.search(prompt):
        return True
    if _TOOL_TRIGGER_RE.search(prompt):
        return True
    if _NON_ASCII_RE.search(prompt):
        return True
    return False


# ---------------------------------------------------------------------------
# Learning journal (Hermes-compatible markdown format)
# ---------------------------------------------------------------------------


class LearningJournal:
    """Append-only markdown learning journal.

    One file per day at ``data/journal/YYYY-MM-DD.md``.
    Format mirrors Hermes so ``loadHermesJournal`` in content.py can parse it.
    """

    def __init__(self, journal_dir: Path = _JOURNAL_DIR) -> None:
        self._dir = journal_dir

    def _today_file(self) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        return self._dir / f"{date.today().isoformat()}.md"

    def record(self, content: str, source: str = "agent", session_id: str = "") -> None:
        """Append a learning entry to today's journal."""
        import hashlib
        import time

        h = hashlib.sha1(f"{content}{time.time()}".encode()).hexdigest()[:8]
        meta = f"source: {source}"
        if session_id:
            meta += f" · session: {session_id}"
        meta += f" · hash: {h}"
        entry = f"\n## {content.strip()}\n> {meta}\n"
        try:
            with open(self._today_file(), "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            logger.warning("LearningJournal.record failed: %s", e)

    def recent(self, days: int = 7) -> List[str]:
        """Return the last N days' learning entries as plain strings."""
        entries: List[str] = []
        for f in sorted(self._dir.glob("*.md"), reverse=True)[:days]:
            try:
                for line in f.read_text(encoding="utf-8").splitlines():
                    if line.startswith("## "):
                        entries.append(line[3:].strip())
            except Exception:
                pass
        return entries


# ---------------------------------------------------------------------------
# Plan parsing
# ---------------------------------------------------------------------------

_STEP_RE = re.compile(
    r"(?:Step\s+\d+|Thought\s+\d+|\d+\.)\s*:?\s*"
    r"\[?(?P<tool>[a-z_]+)\]?\s*[:\-–]\s*(?P<desc>.+)",
    re.IGNORECASE,
)

# Maps natural-language intent → tool name
_INTENT_TO_TOOL: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(fetch|download|get|visit|open|scrape)\b.*(https?://|\burl\b)", re.IGNORECASE), "web_fetch"),
    (re.compile(r"\b(search|google|look up|find|ddg|duckduckgo)\b", re.IGNORECASE), "web_search"),
    (re.compile(r"\b(read|extract|parse|open)\b.*(pdf|docx|document|file|paper)", re.IGNORECASE), "document_extract"),
    (re.compile(r"\b(translate|translation|convert\s+to\s+\w+)\b", re.IGNORECASE), "translate"),
    (
        re.compile(r"\b(explore|analyse|analyze|describe|head|schema|query)\b.*(data|csv|json|jsonl)\b", re.IGNORECASE),
        "data_explore",
    ),
    (re.compile(r"\b(list|find\s+files?|ls|dir|stat|read\s+file|search\s+in\s+file)\b", re.IGNORECASE), "file_explore"),
    (re.compile(r"\b(run|execute|shell|bash|command|cmd)\b", re.IGNORECASE), "shell_run"),
    (re.compile(r"\b(image|photo|picture|analyse\s+image|describe\s+image|ocr)\b", re.IGNORECASE), "image_analyse"),
]


def _infer_tool(description: str) -> str:
    """Infer the best tool name from a step description."""
    for pattern, tool in _INTENT_TO_TOOL:
        if pattern.search(description):
            return tool
    # Default: if there's a URL use web_fetch, else web_search
    if _URL_RE.search(description):
        return "web_fetch"
    return "web_search"


def _extract_params(tool: str, description: str, prompt: str) -> Dict[str, str]:
    """Extract tool parameters from the step description + original prompt."""
    params: Dict[str, str] = {}

    if tool == "web_fetch":
        url_m = _URL_RE.search(description) or _URL_RE.search(prompt)
        params["url"] = url_m.group(0) if url_m else description.strip()

    elif tool == "web_search":
        # Remove the trigger word and use the remainder as query
        query = re.sub(
            r"^\s*(search\s+(for)?|look\s+up|find|google|ddg)\s+", "", description, flags=re.IGNORECASE
        ).strip()
        params["query"] = query or prompt[:200]

    elif tool == "document_extract":
        url_m = _URL_RE.search(description) or _URL_RE.search(prompt)
        pathM = _FILE_PATH_RE.search(description) or _FILE_PATH_RE.search(prompt)
        if url_m:
            params["source"] = url_m.group(0)
        elif pathM:
            params["source"] = pathM.group(1)
        else:
            params["source"] = description.strip()

    elif tool == "translate":
        # Look for "to <lang>" or "into <lang>"
        langM = re.search(r"\b(?:to|into)\s+([a-z\-]{2,10})\b", description, re.IGNORECASE)
        params["target"] = langM.group(1).lower() if langM else "en"
        params["text"] = prompt[:1000]

    elif tool == "data_explore":
        pathM = _FILE_PATH_RE.search(description) or _FILE_PATH_RE.search(prompt)
        params["path"] = pathM.group(1) if pathM else description.strip()
        opM = re.search(r"\b(schema|head|describe|query)\b", description, re.IGNORECASE)
        params["operation"] = opM.group(1).lower() if opM else "head"

    elif tool == "file_explore":
        pathM = _FILE_PATH_RE.search(description) or _FILE_PATH_RE.search(prompt)
        params["path"] = pathM.group(1) if pathM else "."
        opM = re.search(r"\b(list|read|search|stat|find)\b", description, re.IGNORECASE)
        params["operation"] = opM.group(1).lower() if opM else "list"
        if params["operation"] == "search":
            params["arg"] = re.sub(r".*search\s+(for\s+)?", "", description, flags=re.IGNORECASE).strip()

    elif tool == "shell_run":
        cmd_m = re.search(r"[`\"](.+?)[`\"]", description)
        params["command"] = cmd_m.group(1) if cmd_m else description.strip()

    elif tool == "image_analyse":
        pathM = _FILE_PATH_RE.search(description) or _FILE_PATH_RE.search(prompt)
        params["path"] = pathM.group(1) if pathM else description.strip()

    return params


# ---------------------------------------------------------------------------
# Plan-Execute loop
# ---------------------------------------------------------------------------

# Maximum tool steps before synthesising with what we have
_MAX_STEPS = 6
# Maximum context characters carried into final synthesis
_MAX_CONTEXT = 12_000


class PlanExecuteLoop:
    """Decompose a prompt into steps, execute each via tools, synthesise via ToT.

    The loop uses TinyToT's own ToT engine (``generateReasoningResponse``) for
    both planning and synthesis — no external LLM needed.
    """

    def __init__(self, journal: Optional[LearningJournal] = None) -> None:
        from .tools_ext import registry as tool_registry

        self._tools = tool_registry
        self._journal = journal or LearningJournal()

    def run(self, prompt: str, session_id: str = "") -> str:
        """Full plan → execute → synthesise cycle."""
        # Fast path: date/time queries — use shell directly, no planning needed
        if re.search(
            r"\b(?:what\s+(?:day|time|date|is\s+today)|today.s\s+date|current\s+(?:date|time))\b",
            prompt,
            re.IGNORECASE,
        ):
            result = self._tools.run("shell_run", command="date '+%A, %B %d %Y — %H:%M %Z'")
            if result and "exit_code: 0" in result:
                date_str = result.split("stdout:")[-1].strip().split("\n")[0].strip()
                return f"Today is {date_str}."

        steps = self._plan(prompt)
        context_parts: List[str] = []

        for i, (tool_name, params) in enumerate(steps[:_MAX_STEPS], 1):
            logger.info("Agent step %d/%d: %s(%s)", i, len(steps), tool_name, list(params.keys()))
            result = self._tools.run(tool_name, **params)
            if result and not result.startswith("[") or (result.startswith("[") and "error" not in result.lower()):
                label = f"[{tool_name} result]"
                context_parts.append(f"{label}\n{result[: _MAX_CONTEXT // _MAX_STEPS]}")
                # Record useful findings to journal
                if len(result) > 200 and session_id:
                    summary = result[:300].replace("\n", " ")
                    self._journal.record(f"Researched: {prompt[:80]} → {summary}", session_id=session_id)

        if not context_parts:
            # No tool produced useful output — fall through to pure ToT
            return self._synthesise(prompt, "")

        context = "\n\n".join(context_parts)[:_MAX_CONTEXT]
        return self._synthesise(prompt, context)

    def _plan(self, prompt: str) -> List[Tuple[str, Dict[str, str]]]:
        """Return a list of (tool_name, params) tuples for this prompt."""
        # Fast path: single-step prompts
        if not _MULTI_STEP_RE.search(prompt) and len(prompt.split()) < 20:
            tool = _infer_tool(prompt)
            params = _extract_params(tool, prompt, prompt)
            return [(tool, params)]

        # Use ToT to generate a mini plan — call generateTreeOfThoughtsResponse
        # directly to avoid re-entering the agent dispatch loop.
        plan_prompt = (
            "Create a step-by-step plan to answer the following request. "
            "For each step, write: 'Step N: [tool_name] - description'\n"
            "Available tools: web_fetch, web_search, document_extract, translate, "
            "data_explore, file_explore, shell_run, image_analyse\n\n"
            f"Request: {prompt}"
        )
        try:
            from .inference import generateTreeOfThoughtsResponse

            plan_text = generateTreeOfThoughtsResponse(plan_prompt)
        except Exception:
            plan_text = ""

        steps: List[Tuple[str, Dict[str, str]]] = []
        for line in plan_text.splitlines():
            m = _STEP_RE.match(line.strip())
            if m:
                tool_raw = m.group("tool").lower()
                desc = m.group("desc").strip()
                # Match to known tool names
                tool = tool_raw if self._tools.get(tool_raw) else _infer_tool(desc)
                params = _extract_params(tool, desc, prompt)
                steps.append((tool, params))

        # Fallback: extract from prompt directly
        if not steps:
            tool = _infer_tool(prompt)
            params = _extract_params(tool, prompt, prompt)
            steps = [(tool, params)]

        return steps[:_MAX_STEPS]

    def _synthesise(self, prompt: str, context: str) -> str:
        """Run ToT over the accumulated context, then translate if the prompt requests it.

        Detects "answer/respond in <language>" instructions and automatically
        translates the English reasoning output to the target language.
        """
        from .inference import generateTreeOfThoughtsResponse
        from .tools_ext import TranslateTool

        synthesis_prompt = (
            f"{prompt}\n\nUse the following gathered information to answer:\n\n{context}" if context else prompt
        )

        # Detect explicit language output requests
        langM = re.search(
            r"\b(?:answer|respond|reply|explain|give.*advice|tell.*me)\s+in\s+"
            r"(" + LANG_NAMES_PATTERN + r")\b",
            prompt,
            re.IGNORECASE,
        )
        lang_result = Lang.from_name(langM.group(1)) if langM else None
        target_lang = lang_result.code if lang_result else None

        # Also detect if the prompt itself is non-ASCII — infer desired output language
        if not target_lang and _NON_ASCII_RE.search(prompt):
            detected = detect_lang(prompt)
            target_lang = detected.code if detected else None

        # Generate English reasoning (skip knowledge grounding for foreign-language prompts
        # to avoid cross-domain passage contamination)
        english_result = generateTreeOfThoughtsResponse(
            synthesis_prompt,
            skip_knowledge=bool(target_lang),
        )

        if not target_lang:
            return english_result

        # Extract the clean conclusion for translation
        if "Complete reasoning from optimal path:" in english_result:
            tail = english_result.split("Complete reasoning from optimal path:")[-1]
            lines = [
                ln.strip()
                for ln in tail.splitlines()
                if ln.strip() and not ln.startswith("Learning from") and not ln.startswith("Context:")
            ]
            english_clean = "\n".join(lines[:15])
        else:
            english_clean = english_result[:800]

        translated = TranslateTool().run(text=english_clean, target=target_lang, source="en")
        return translated


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

_loop = PlanExecuteLoop()
_journal = _loop._journal


def agentResponse(prompt: str, session_id: str = "") -> str:
    """Entry point called from ``generateReasoningResponse`` when agent mode fires."""
    return _loop.run(prompt, session_id=session_id)
