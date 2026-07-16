"""
tinytot.content — chain loading, category discovery, schema parsing.

All I/O lives here. Every public function is pure or @lru_cache so
it can be tested without a running server.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

import frontmatter
import yaml

logger = logging.getLogger(__name__)

__all__ = [
    "getCategories",
    "loadReasoningChains",
    "loadToolPatterns",
    "loadKnowledgePassages",
    "loadHermesJournal",
    "getVariantConfig",
]

# ---------------------------------------------------------------------------
# Path configuration (override via environment or pass explicitly in tests)
# ---------------------------------------------------------------------------


def _find_package_data_dir() -> Path:
    """Locate the bundled tinytot/_data/ directory (always the base install)."""
    if sys.version_info >= (3, 9):
        import importlib.resources as _ir

        return Path(str(_ir.files("tinytot").joinpath("_data")))

    try:
        import importlib_resources as _ir  # type: ignore[import]

        return Path(str(_ir.files("tinytot").joinpath("_data")))
    except ImportError:
        pass

    return Path(__file__).parent / "_data"


def _find_data_dir() -> Path:
    """Return the active data directory.

    Priority:
      1. TINYTOT_DATA_DIR env var — points to a variant delta directory created
         by ``tinytot-clone``.  Files found here override the base install.
      2. The bundled tinytot/_data/ inside the installed package.

    Two-level overlay: when TINYTOT_DATA_DIR is set, use it as the *delta* dir.
    The base package data is always available as BASE_DATA_DIR.  Resolution
    helpers (e.g. loadKnowledgePassages) merge both layers so variants only need
    to ship the files they actually change.
    """
    if env := os.environ.get("TINYTOT_DATA_DIR"):
        return Path(env)

    # importlib.resources.files() requires Python 3.9+; use the backport on 3.8.
    if sys.version_info >= (3, 9):
        import importlib.resources as _ir

        return Path(str(_ir.files("tinytot").joinpath("_data")))

    try:
        import importlib_resources as _ir  # type: ignore[import]

        return Path(str(_ir.files("tinytot").joinpath("_data")))
    except ImportError:
        pass

    # Final fallback for editable installs where importlib_resources isn't present
    return Path(__file__).parent / "_data"


BASE_DATA_DIR = _find_package_data_dir()  # always the bundled package data
DATA_DIR = _find_data_dir()  # variant delta dir, or same as BASE_DATA_DIR

CATEGORY_DIR = DATA_DIR / "categories"
SCHEMA_FILE = DATA_DIR / "schema" / "information_patterns.md"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
VARIANTS_DIR = BASE_DATA_DIR / "variants"  # variant templates always from base

# ---------------------------------------------------------------------------
# Compiled regex (module-level so they are shared across the package)
# ---------------------------------------------------------------------------

COMPILED_CHAIN_HEADER = re.compile(r"## Chain(?:\s+\d+)?:\s*(.+)")
COMPILED_HANDLES_COMMENT = re.compile(r"<!-- Handles: (.+) -->")
COMPILED_THOUGHT = re.compile(r"Thought \d+: (.+)")
COMPILED_CONCLUSION = re.compile(r"Conclusion:\s*(.+)")
COMPILED_WORD_SHORT = re.compile(r"\b\w{3,}\b")
COMPILED_WORD_LONG = re.compile(r"\b\w{4,}\b")

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Chain = Tuple[str, List[str], Dict[str, Any]]  # (title, thoughts, metadata)

# ---------------------------------------------------------------------------
# Category discovery
# ---------------------------------------------------------------------------

YAML_DELIMITER = "---"
YAML_START_OFFSET = 3
METADATA_KEY_CATEGORY = "category"
METADATA_KEY_HANDLES = "handles"


@lru_cache(maxsize=1)
def getCategories(categoryDir: Path = CATEGORY_DIR) -> Dict[str, str]:
    """Return {category_name: filename} for every .md file under categoryDir."""
    categories: Dict[str, str] = {}
    if not categoryDir.exists():
        return categories

    for mdFile in categoryDir.glob("*.md"):
        categoryName = mdFile.stem
        try:
            content = mdFile.read_text(encoding="utf-8")
            if content.startswith(YAML_DELIMITER):
                end = content.find(YAML_DELIMITER, YAML_START_OFFSET)
                if end != -1:
                    header = content[YAML_START_OFFSET:end].strip()
                    try:
                        meta = yaml.safe_load(header)
                        if meta and METADATA_KEY_CATEGORY in meta:
                            categoryName = meta[METADATA_KEY_CATEGORY]
                    except yaml.YAMLError as e:
                        logger.warning("YAML parse error in %s: %s", mdFile, e)
        except (IOError, OSError) as e:
            logger.warning("Cannot read %s: %s", mdFile, e)

        categories[categoryName] = mdFile.name

    return categories


# ---------------------------------------------------------------------------
# Chain loading
# ---------------------------------------------------------------------------


@lru_cache(maxsize=None)
def loadReasoningChains(categoryFile: str, categoryDir: Path = CATEGORY_DIR) -> List[Chain]:
    """Parse a category markdown file and return all reasoning chains.

    Cached per filename — disk is only read once per process lifetime.
    """
    filePath = categoryDir / categoryFile
    if not filePath.exists():
        return []

    chains: List[Chain] = []
    currentChain: List[str] = []
    currentTitle = ""
    currentMeta: Dict[str, Any] = {}

    for line in filePath.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if line.startswith("## Chain"):
            if currentChain:
                chains.append((currentTitle, currentChain, currentMeta))
            m = COMPILED_CHAIN_HEADER.match(line)
            currentTitle = m.group(1) if m else f"Chain {len(chains) + 1}"
            currentChain = []
            currentMeta = {}

        elif line.startswith("<!-- Handles:"):
            m = COMPILED_HANDLES_COMMENT.match(line)
            if m:
                currentMeta[METADATA_KEY_HANDLES] = [h.strip() for h in m.group(1).split(",")]

        elif line.startswith("Thought"):
            m = COMPILED_THOUGHT.match(line)
            if m:
                currentChain.append(m.group(1))

        elif line.startswith("Conclusion:"):
            m = COMPILED_CONCLUSION.match(line)
            if m:
                currentMeta["conclusion"] = m.group(1).strip()

    if currentChain:
        chains.append((currentTitle, currentChain, currentMeta))

    return chains


# ---------------------------------------------------------------------------
# Schema / tool pattern loading
# ---------------------------------------------------------------------------


def loadToolPatterns(schemaFile: Path = SCHEMA_FILE) -> List[Dict[str, Any]]:
    """Parse the information_patterns.md schema into a list of tool pattern dicts."""
    if not schemaFile.exists():
        return []

    try:
        post = frontmatter.load(str(schemaFile))
        content = post.content
    except Exception as e:
        logger.warning("Cannot load schema %s: %s", schemaFile, e)
        return []

    patterns: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    inToolSection = False

    for line in content.split("\n"):
        line = line.strip()

        if line.startswith("## "):
            if current:
                patterns.append(current)
            current = {"name": line[3:].lower().replace(" ", "_")}
            inToolSection = True
            continue

        if not inToolSection or not line.startswith("- "):
            continue

        if ": " in line:
            key, value = line[2:].split(": ", 1)
            key, value = key.strip(), value.strip()
            if key in ("keywords", "exclude_keywords"):
                current[key] = [k.strip() for k in value.split(",")]
            elif key == "params":
                try:
                    current[key] = json.loads(value)
                except json.JSONDecodeError:
                    current[key] = {}
            else:
                current[key] = value

    if current:
        patterns.append(current)

    return patterns


# ---------------------------------------------------------------------------
# Knowledge base loading
# ---------------------------------------------------------------------------

# (heading, passage_text)
KnowledgePassage = Tuple[str, str]

# Matches the Hermes provenance blockquote:
# > source: agent · 2026-01-15T14:32:00+00:00 · hash: 3a7fbc…
_HERMES_META_RE = re.compile(r"^>\s*source:\s*\S+\s+\S\s+\S+\s+\S\s+hash:\s+[a-f0-9]{64}")


def _isHermesJournal(lines: List[str]) -> bool:
    """Return True if the file contains at least one Hermes provenance line."""
    return any(_HERMES_META_RE.match(line.rstrip()) for line in lines)


def loadHermesJournal(path: Path) -> List[KnowledgePassage]:
    """Parse a Hermes Learning Journal file into knowledge passages.

    The Hermes journal format uses ``## <content>`` headings as learning entries,
    each followed by a ``> source: ... · hash: ...`` provenance line. This function
    extracts the content of each such heading as a passage, stripping the metadata.
    Ordinary section headings without a following provenance line are section labels.

    This is the bridge between Hermes organic learning and TinyToT inference:
    learnings recorded in Hermes sessions become directly retrievable knowledge
    in TinyToT without any training step.
    """
    if not path.exists():
        return []

    passages: List[KnowledgePassage] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    section = ""
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Top-level heading (#) — section label only, not a passage
        if line.startswith("# ") and not line.startswith("## "):
            section = line.lstrip("#").strip()
            i += 1
            continue

        # Learning entry: ## <content>
        if line.startswith("## "):
            content = line[3:].strip()

            # Look ahead past blank lines to find provenance
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1

            if j < len(lines) and _HERMES_META_RE.match(lines[j].rstrip()):
                # Valid learning entry — record as a passage
                if content:
                    passages.append((section, content))
                i = j + 1  # skip past the provenance line
                continue

        i += 1

    return passages


@lru_cache(maxsize=None)
def loadKnowledgePassages(
    knowledgeDir: Path = KNOWLEDGE_DIR,
) -> List[KnowledgePassage]:
    """Load all passages from every .md file in knowledgeDir.

    Supports two file formats automatically:
    - **Hermes journal** (``## learning \\n> source: ... · hash: ...``) —
      each ``##`` heading is a learning entry; provenance metadata is stripped.
    - **Plain knowledge** — each non-empty paragraph is a passage.

    **Overlay / delta support**: when TINYTOT_DATA_DIR points to a variant
    delta dir, passages are loaded from the base package knowledge first,
    then the delta knowledge dir is merged on top — files with the same stem
    replace base passages; new files add to the corpus.  This means a variant
    only needs to ship the files it actually changes.

    Cached per directory path. Restart the server after editing knowledge files.
    """
    base_knowledge = BASE_DATA_DIR / "knowledge"

    # Overlay only activates for the default knowledge dir (i.e. the server's active
    # knowledge path).  When called with an explicit custom dir (tests, evals, etc.),
    # load only that dir — no base merging.
    use_overlay = knowledgeDir == KNOWLEDGE_DIR and knowledgeDir != base_knowledge

    if use_overlay:
        # Collect the set of .md files to load, with delta files overriding base
        file_map: Dict[str, Path] = {}  # stem → path (last writer wins)
        for md_file in sorted(base_knowledge.glob("*.md")):
            file_map[md_file.stem] = md_file
        if knowledgeDir.exists():
            for md_file in sorted(knowledgeDir.glob("*.md")):
                file_map[md_file.stem] = md_file  # override or add
        md_files = sorted(file_map.values(), key=lambda p: p.name)
    else:
        if not knowledgeDir.exists():
            return []
        md_files = sorted(knowledgeDir.glob("*.md"))

    passages: List[KnowledgePassage] = []
    currentHeading = ""

    for md_file in md_files:
        try:
            lines = md_file.read_text(encoding="utf-8").splitlines()
        except (IOError, OSError) as e:
            logger.warning("Cannot read knowledge file %s: %s", md_file, e)
            continue

        if _isHermesJournal(lines):
            passages.extend(loadHermesJournal(md_file))
            continue

        # Plain knowledge format: paragraph-per-passage
        currentPara: List[str] = []

        def flush(heading: str, para: List[str]) -> None:
            text = " ".join(para).strip()
            if text:
                passages.append((heading, text))

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                flush(currentHeading, currentPara)
                currentPara = []
                currentHeading = stripped.lstrip("#").strip()
            elif stripped == "":
                flush(currentHeading, currentPara)
                currentPara = []
            else:
                currentPara.append(stripped)

        flush(currentHeading, currentPara)

    return passages


# ---------------------------------------------------------------------------
# Variant configuration
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def getVariantConfig(dataDir: Path = DATA_DIR) -> Dict[str, Any]:
    """Return the variant config for this data directory, or {} for the base install.

    A variant is identified by a ``variant.yaml`` file at the root of the delta
    data directory (written by ``tinytot-clone --variant``).  If no such file
    exists, returns an empty dict (base TinyToT behaviour unchanged).
    """
    variant_file = dataDir / "variant.yaml"
    if not variant_file.exists():
        return {}
    try:
        return yaml.safe_load(variant_file.read_text(encoding="utf-8")) or {}
    except Exception as e:
        logger.warning("Cannot load variant config %s: %s", variant_file, e)
        return {}
