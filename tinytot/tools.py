"""
tinytot.tools — tool detection, parameter extraction, MCP tool matching.

Depends only on tinytot.content. No FastAPI imports.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .content import SCHEMA_FILE, loadToolPatterns

logger = logging.getLogger(__name__)

__all__ = [
    "extractTopic",
    "detectToolUsage",
    "matchToolFromAvailable",
    "detectInformationNeed",
]

TOOL_NAME_SEPARATOR = "__"
TOOL_NAME_DASH = "_"
TOOL_MATCH_STRONG = 10
TOOL_MATCH_PREFIX = 5

# ---------------------------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------------------------

_ACTION_WORDS = frozenset({"search", "find", "tell", "show", "get", "what", "who", "where", "when", "how"})
_SKIP_WORDS = frozenset(
    {
        "me",
        "about",
        "for",
        "in",
        "on",
        "at",
        "by",
        "with",
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
    }
)


def extractTopic(prompt: str) -> str:
    """Extract the main subject from a prompt by skipping action/stop words."""
    words = prompt.lower().split()
    i = 0
    while i < len(words) and words[i] in _ACTION_WORDS:
        i += 1
    while i < len(words) and words[i] in _SKIP_WORDS:
        i += 1

    remaining = words[i : i + 5]
    while remaining and remaining[-1] in _SKIP_WORDS:
        remaining.pop()

    return " ".join(remaining) if remaining else prompt[:100]


# ---------------------------------------------------------------------------
# Tool detection
# ---------------------------------------------------------------------------


def detectToolUsage(prompt: str, schemaFile: Path = SCHEMA_FILE) -> Tuple[Optional[str], Dict[str, Any]]:
    """Return (tool_name, params) if prompt matches a schema tool pattern, else (None, {})."""
    patterns = loadToolPatterns(schemaFile)
    promptLower = prompt.lower()

    for pattern in patterns:
        keywords: List[str] = pattern.get("keywords", [])
        excludes: List[str] = pattern.get("exclude_keywords", [])

        if any(ex in promptLower for ex in excludes):
            continue

        matched = False
        for kw in keywords:
            if ".*" in kw:
                try:
                    if re.search(kw, promptLower, re.IGNORECASE):
                        matched = True
                        break
                except re.error:
                    continue
            elif kw.lower() in promptLower:
                matched = True
                break

        if not matched:
            continue

        toolName: str = pattern.get("tool_name", "")
        paramsTemplate: Dict[str, Any] = pattern.get("params", {})

        params: Dict[str, Any] = {}
        for key, value in paramsTemplate.items():
            if isinstance(value, str) and value == "extract_topic":
                params[key] = extractTopic(prompt)
            elif isinstance(value, str) and value == "full_prompt":
                params[key] = prompt
            else:
                params[key] = value

        return toolName, params

    return None, {}


# ---------------------------------------------------------------------------
# MCP tool matching
# ---------------------------------------------------------------------------


def matchToolFromAvailable(toolName: str, availableTools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Match an internal tool name to the best available MCP tool function dict."""
    best: Optional[Dict[str, Any]] = None
    bestScore = 0

    normName = toolName.lower().replace("-", TOOL_NAME_DASH)
    prefix = normName.split("_")[0]

    for tool in availableTools:
        if tool.get("type") != "function":
            continue
        func = tool.get("function", {})
        funcName = func.get("name", "").lower()
        serverName = funcName.split(TOOL_NAME_SEPARATOR)[0]

        score = 0
        if normName in serverName:
            score = TOOL_MATCH_STRONG
        elif prefix in serverName:
            score = TOOL_MATCH_PREFIX

        if score > bestScore:
            bestScore = score
            best = func

    return best


# ---------------------------------------------------------------------------
# Information need heuristic (used as fallback in categorization)
# ---------------------------------------------------------------------------


def detectInformationNeed(prompt: str) -> bool:
    """Return True if the prompt likely needs external information lookup."""
    lower = prompt.lower()
    words = lower.split()

    question_words = {"what", "when", "where", "why", "how", "who", "which"}
    if question_words.intersection(words[:3]):
        return True

    temporal = {"recent", "latest", "current", "today", "now", "update", "developments"}
    if any(w in lower for w in temporal):
        return True

    research = {"explain", "understand", "analyze", "investigate", "research", "study", "examine"}
    if any(w in lower for w in research):
        return True

    origWords = prompt.split()
    if len(origWords) > 1:
        capitalized = [w for w in origWords[1:] if w and w[0].isupper() and len(w) > 2]
        if capitalized:
            return True

    return False
