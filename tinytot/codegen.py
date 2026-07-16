"""
tinytot.codegen -- Dataset-driven code generation.

All code templates live in data/codegen/templates/<key>.md.
All pattern-to-key mappings live in data/codegen/patterns.yaml.
All compositional decompositions live in data/codegen/decompositions.yaml.
Language detection, request detection, and fence labels live in data/codegen/config.yaml.

This module is a thin loader and dispatcher -- no hardcoded code strings,
language lists, or request-detection patterns.

Architecture:
    isCodeRequest(prompt)    -- detect code-writing prompts (via config.yaml)
    detectLanguage(prompt)   -- identify target language   (via config.yaml)
    generateCode(prompt)     -- dispatch: match pattern -> load template -> return block
    _loadTemplate(key, lang) -- read from data/codegen/templates/<key>.md
    _loadPatterns()          -- read from data/codegen/patterns.yaml
    _loadConfig()            -- read from data/codegen/config.yaml
    _loadDecompositions()    -- read from data/codegen/decompositions.yaml
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

__all__ = [
    "generateCode",
    "generateProject",
    "detectCodeRequest",
    "isCodeRequest",
    "detectLanguage",
    "isProjectRequest",
]

from tinytot.content import DATA_DIR as _TINYTOT_DATA_DIR

_DATA_DIR = _TINYTOT_DATA_DIR / "codegen"
_TEMPLATES_DIR = _DATA_DIR / "templates"
_PATTERNS_FILE = _DATA_DIR / "patterns.yaml"
_DECOMPOSITIONS_FILE = _DATA_DIR / "decompositions.yaml"
_CONFIG_FILE = _DATA_DIR / "config.yaml"
_PROJECTS_FILE = _DATA_DIR / "projects.yaml"

# ---------------------------------------------------------------------------
# Structural extraction patterns (these are about Python syntax, not domain)
# ---------------------------------------------------------------------------

_FUNC_NAME_RE = re.compile(
    r"\bfunction\s+(?:called|named|to)\s+['\"]?(\w+)['\"]?",
    re.IGNORECASE,
)
_CLASS_NAME_RE = re.compile(
    r"\bclass\s+(?:called|named|for)?\s*['\"]?([A-Z][A-Za-z]\w*)['\"]?",
)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _loadConfig() -> dict:
    """Load language detection and request patterns from config.yaml."""
    if not _CONFIG_FILE.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(_CONFIG_FILE.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _loadPatterns() -> list[tuple[re.Pattern[str], str]]:
    """Load pattern->key mappings from patterns.yaml."""
    if not _PATTERNS_FILE.exists():
        return []
    try:
        import yaml

        data = yaml.safe_load(_PATTERNS_FILE.read_text(encoding="utf-8"))
        return [(re.compile(entry["pattern"], re.IGNORECASE), entry["key"]) for entry in data.get("patterns", [])]
    except Exception:
        return []


@lru_cache(maxsize=1)
def _loadDecompositions() -> dict:
    """Load compositional decomposition table from decompositions.yaml."""
    if not _DECOMPOSITIONS_FILE.exists():
        return {}
    try:
        import yaml

        data = yaml.safe_load(_DECOMPOSITIONS_FILE.read_text(encoding="utf-8"))
        return data.get("decompositions", {})
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Language detection (data-driven via config.yaml)
# ---------------------------------------------------------------------------


def detectLanguage(prompt: str) -> str:
    """Return the canonical language name for a prompt, or the default."""
    cfg = _loadConfig()
    languages = cfg.get("languages", [])
    sql_keywords = cfg.get("sql_keywords", [])
    default = cfg.get("default_language", "python")

    # Try each language pattern in order
    for entry in languages:
        if re.search(entry["match"], prompt, re.IGNORECASE):
            return entry["name"]

    # Check if it looks like SQL
    if any(re.search(kw, prompt, re.IGNORECASE) for kw in sql_keywords):
        return "sql"

    return default


# ---------------------------------------------------------------------------
# Code request detection (data-driven via config.yaml)
# ---------------------------------------------------------------------------


def isCodeRequest(prompt: str) -> bool:
    """Return True if the prompt is asking for code to be written.

    Uses request_patterns from config.yaml, plus any template pattern match.
    """
    cfg = _loadConfig()
    for pat_str in cfg.get("request_patterns", []):
        if re.search(pat_str, prompt, re.IGNORECASE):
            return True

    # Also treat SQL keywords + SQL verbs as code requests
    sql_keywords = cfg.get("sql_keywords", [])
    sql_verbs = {"select", "insert", "update", "delete", "create table", "join", "query"}
    if any(re.search(kw, prompt, re.IGNORECASE) for kw in sql_keywords):
        if any(v in prompt.lower() for v in sql_verbs):
            return True

    # If a template pattern matches, it's a code request
    return _matchPattern(prompt) is not None


# ---------------------------------------------------------------------------
# Template loading
# ---------------------------------------------------------------------------


def _loadTemplate(key: str, language: str) -> Optional[str]:
    """Load the code snippet for (key, language) from the template file.

    Parses ## <language> sections and returns the content without fences.
    Supports fence label aliases (c++ -> cpp, c# -> csharp).
    """
    template_file = _TEMPLATES_DIR / f"{key}.md"
    if not template_file.exists():
        return None
    content = template_file.read_text(encoding="utf-8")

    # Build language variant list from config fence_labels
    cfg = _loadConfig()
    fence_labels = cfg.get("fence_labels", {})
    # Invert: canonical -> [canonical, fence_label] and fence_label -> canonical
    variants = [language]
    if language in fence_labels:
        variants.append(fence_labels[language])
    # Also accept the fence label as a section header
    for canon, fence in fence_labels.items():
        if fence == language:
            variants.append(canon)

    sections: dict[str, str] = {}
    current_lang: Optional[str] = None
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_lang is not None:
                sections[current_lang] = "\n".join(current_lines).strip()
            current_lang = line[3:].strip().lower()
            current_lines = []
        elif current_lang is not None:
            current_lines.append(line)

    if current_lang is not None:
        sections[current_lang] = "\n".join(current_lines).strip()

    for variant in variants:
        section = sections.get(variant.lower())
        if section:
            lines = section.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines).strip()
            # Python 3.8 compat: add __future__.annotations if code uses
            # inline generics (list[int], dict[str, int], etc.)
            if language.lower() in ("python", "python3") and re.search(
                r"\b(?:list|dict|tuple|set|frozenset|type)\[\w",
                code,
            ):
                code = "from __future__ import annotations\n\n" + code
            return code

    return None


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------


def _matchPattern(prompt: str) -> Optional[str]:
    """Return the first template key whose pattern matches the prompt."""
    for pat, key in _loadPatterns():
        if pat.search(prompt):
            return key
    return None


# ---------------------------------------------------------------------------
# Code request metadata
# ---------------------------------------------------------------------------


@dataclass
class CodeRequest:
    language: str = "python"
    task: str = ""
    func_name: str = ""
    params: list[str] = field(default_factory=list)
    return_hint: str = ""
    container: str = ""
    class_name: str = ""
    raw_prompt: str = ""


def detectCodeRequest(prompt: str) -> CodeRequest:
    """Parse a code-generation prompt into a structured CodeRequest."""
    req = CodeRequest(raw_prompt=prompt)
    req.language = detectLanguage(prompt)
    req.task = prompt.strip()

    lower = prompt.lower()
    if "class" in lower:
        req.container = "class"
        m = _CLASS_NAME_RE.search(prompt)
        req.class_name = m.group(1) if m else ""
    elif "query" in lower or req.language == "sql":
        req.container = "query"
    elif "script" in lower or "program" in lower:
        req.container = "script"
    else:
        req.container = "function"

    m = _FUNC_NAME_RE.search(prompt)
    if m:
        req.func_name = m.group(1)

    return req


# ---------------------------------------------------------------------------
# Compositional inference
# ---------------------------------------------------------------------------


def _composeCode(key: str, language: str) -> Optional[str]:
    """Return the template with a decomposition header when sub-problems exist."""
    decomps = _loadDecompositions()
    decomp = decomps.get(key, {})
    code = _loadTemplate(key, language)
    if not code:
        return None

    sub_problems = decomp.get("composes", [])
    if not sub_problems:
        return code

    header = [
        f"# Composition: {decomp.get('description', key)}",
        "# Built from: " + " + ".join(s["template"] for s in sub_problems),
        "# Steps:",
    ]
    for i, step in enumerate(sub_problems, 1):
        header.append(f"#   {i}. {step.get('role', step['template'])}")
    header.append("")

    return "\n".join(header) + code


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def formatCodeBlock(code: str, language: str) -> str:
    """Wrap code in a fenced markdown code block using config fence labels."""
    cfg = _loadConfig()
    fence_lang = cfg.get("fence_labels", {}).get(language, language)
    return f"```{fence_lang}\n{code}\n```"


def generateCode(prompt: str) -> Optional[str]:
    """Generate code for a code-writing prompt.

    Returns a fenced markdown code block, or None if no pattern matches.
    """
    key = _matchPattern(prompt)
    if not key:
        return None

    language = detectLanguage(prompt)

    decomps = _loadDecompositions()
    if key in decomps and decomps[key].get("composes"):
        code = _composeCode(key, language)
    else:
        code = _loadTemplate(key, language)

    if not code:
        # Language not in template -- fall back to Python with a note
        code = _loadTemplate(key, "python")
        if code:
            code = f"# Note: {language} template not yet available. Showing Python:\n\n" + code
            language = "python"

    if not code:
        return None

    return formatCodeBlock(code, language)


# ---------------------------------------------------------------------------
# Project scaffolding (Tier 3)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _loadProjects() -> dict:
    """Load project blueprints from projects.yaml."""
    if not _PROJECTS_FILE.exists():
        return {}
    try:
        import yaml

        data = yaml.safe_load(_PROJECTS_FILE.read_text(encoding="utf-8"))
        return data.get("projects", {})
    except Exception:
        return {}


def _matchProject(prompt: str) -> Optional[tuple[str, dict]]:
    """Return (project_key, blueprint) for the first matching project pattern."""
    projects = _loadProjects()
    for key, blueprint in projects.items():
        for pat_str in blueprint.get("patterns", []):
            if re.search(pat_str, prompt, re.IGNORECASE):
                return key, blueprint
    return None


def isProjectRequest(prompt: str) -> bool:
    """Return True if the prompt is asking for a multi-file project scaffold."""
    return _matchProject(prompt) is not None


def generateProject(prompt: str) -> Optional[str]:
    """Generate a multi-file project scaffold as a structured response.

    Returns a Markdown document containing all project files as fenced code
    blocks with their file paths, or None if no blueprint matches.
    """
    match = _matchProject(prompt)
    if not match:
        return None

    key, blueprint = match
    description = blueprint.get("description", key)
    files = blueprint.get("files", [])

    parts = [
        f"## Project: {description}",
        "",
        f"Generated {len(files)} file{'s' if len(files) != 1 else ''}:",
        "",
    ]

    for file_spec in files:
        path = file_spec.get("path", "unknown")
        note = file_spec.get("note", "")
        content = file_spec.get("content", "")
        template_key = file_spec.get("template")
        language = file_spec.get("language", "python")

        if not content and template_key:
            content = _loadTemplate(template_key, language) or ""

        if not content:
            continue

        # Determine fence language from file extension
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        fence_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "go": "go",
            "rs": "rust",
            "java": "java",
            "toml": "toml",
            "yaml": "yaml",
            "yml": "yaml",
            "json": "json",
            "md": "markdown",
            "txt": "",
            "sh": "bash",
            "sql": "sql",
        }
        fence_lang = fence_map.get(ext, ext)

        header = f"### `{path}`"
        if note:
            header += f"  *— {note}*"
        parts.append(header)
        parts.append(f"```{fence_lang}")
        parts.append(content.strip())
        parts.append("```")
        parts.append("")

    parts.append("---")
    parts.append("*Files above are ready to copy into your project directory.*")

    return "\n".join(parts)
