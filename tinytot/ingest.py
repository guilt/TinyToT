"""
tinytot.ingest — Convert external reasoning trace corpora into TinyToT-native formats.

Each source is a subcommand.  New sources can be added by implementing an
``IngestSource`` and registering it in ``_SOURCES``.

Built-in sources
----------------
gsm8k
    Grade-school math JSONL → data/knowledge/gsm8k_test.md
tot-princeton
    Clones (or updates) https://github.com/princeton-nlp/tree-of-thought-llm
    into data/.sources/tree-of-thought-llm, then ingests every supported
    trace file found there:
      • game24  → data/categories/game24.md
      • text    → data/categories/creative_writing.md
translate-packs
    Downloads argostranslate language packs for offline translation.
    Installs pairs needed for the benchmark suite by default.

Usage
-----
    pipenv run python -m tinytot.ingest gsm8k data/gsm8k_test.jsonl
    pipenv run python -m tinytot.ingest tot-princeton
    pipenv run python -m tinytot.ingest translate-packs
    pipenv run python -m tinytot.ingest all
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from tinytot.content import CATEGORY_DIR, DATA_DIR, KNOWLEDGE_DIR

from .lang import TRANSLATE_LANGS, TRANSLATE_PAIRS  # noqa: F401 (re-exported for CLI use)

logger = logging.getLogger(__name__)

SOURCES_DIR = DATA_DIR / ".sources"

# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class IngestSource(ABC):
    """One corpus that can be fetched and ingested."""

    name: str
    help: str
    label: str = ""  # display title for _print_section; defaults to name

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser) -> None:
        """Register any extra CLI arguments this source needs."""

    @abstractmethod
    def run(self, args: argparse.Namespace) -> list[tuple[str, int, Path]]:
        """Fetch and ingest.  Returns list of (label, count, out_path) tuples."""


# ---------------------------------------------------------------------------
# GSM8K
# ---------------------------------------------------------------------------

_CALC_RE = re.compile(r"<<[^>]+>>")


def _cleanGsm(text: str) -> str:
    return _CALC_RE.sub("", text).strip()


def _iterGsm8k(path: Path) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _gsm8kToPassage(record: dict) -> str:
    question = record["question"].strip()
    rawAnswer = record["answer"]
    if "####" in rawAnswer:
        stepsRaw, final = rawAnswer.split("####", 1)
        steps = _cleanGsm(stepsRaw).strip()
        answer = final.strip()
    else:
        steps = _cleanGsm(rawAnswer).strip()
        answer = steps.split("\n")[-1].strip()
    lines = [f"Q: {question}"]
    for i, step in enumerate(steps.splitlines(), 1):
        step = step.strip()
        if step:
            lines.append(f"Step {i}: {step}")
    lines.append(f"Answer: {answer}")
    return "\n".join(lines)


def ingestGsm8k(source: Path, outFile: Path, limit: int = 0) -> int:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    records = list(_iterGsm8k(source))
    if limit:
        records = records[:limit]
    lines = ["# GSM8K Math Reasoning\n", "## Math Problems\n"]
    for rec in records:
        lines.append(_gsm8kToPassage(rec) + "\n")
    outFile.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote %d GSM8K passages to %s", len(records), outFile)
    return len(records)


class GSM8KSource(IngestSource):
    name = "gsm8k"
    label = "Ingest GSM8K Math"
    help = "Ingest GSM8K math JSONL → data/knowledge/gsm8k_test.md"

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "source",
            type=Path,
            nargs="?",
            default=DATA_DIR / "gsm8k_test.jsonl",
            help="Path to GSM8K JSONL (default: data/gsm8k_test.jsonl)",
        )
        parser.add_argument("--out", type=Path, default=KNOWLEDGE_DIR / "gsm8k_test.md")
        parser.add_argument("--limit", type=int, default=0, help="Max records (0=all)")

    def run(self, args: argparse.Namespace) -> list[tuple[str, int, Path]]:
        n = ingestGsm8k(args.source, args.out, args.limit)
        return [("GSM8K", n, args.out)]


# ---------------------------------------------------------------------------
# Princeton ToT helpers
# ---------------------------------------------------------------------------

_PRINCETON_TOT_REPO = "https://github.com/princeton-nlp/tree-of-thought-llm"
_PRINCETON_TOT_DIR = SOURCES_DIR / "tree-of-thought-llm"

# game24 trace → (glob pattern, ingest function, out path)
_PRINCETON_TRACES: list[tuple[str, str]] = [
    (
        "logs/game24/gpt-4_0.7_propose1_value3_greedy5_start900_end1000.json",
        "game24",
    ),
    (
        "logs/text/gpt-4_1.0_generate_sample_select_greedy_sample5_start0_end100.json",
        "text",
    ),
]


def _ensurePrincetonRepo(dest: Path, update: bool = True) -> Path:
    """Clone princeton-nlp/tree-of-thought-llm into dest, or pull if already present."""
    from git import InvalidGitRepositoryError, Repo

    if dest.exists():
        try:
            repo = Repo(dest)
            if update:
                logger.info("Updating %s ...", dest)
                repo.remotes.origin.pull()
            return dest
        except InvalidGitRepositoryError:
            pass

    logger.info("Cloning %s → %s ...", _PRINCETON_TOT_REPO, dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    Repo.clone_from(_PRINCETON_TOT_REPO, dest, depth=1)
    return dest


# ---------------------------------------------------------------------------
# ToT Game24
# ---------------------------------------------------------------------------


def _game24Chain(trace: dict, chain_num: int) -> str | None:
    steps = trace.get("steps", [])
    x = steps[0].get("x", "?") if steps else trace.get("x", "?")
    solutionPath = []
    for step in steps:
        newYs = step.get("new_ys", [])
        if newYs:
            solutionPath.append(newYs[0].strip().replace("\n", " → "))
    if not solutionPath:
        return None
    infos = trace.get("infos", [])
    solved = any(i.get("r", 0) == 1 for i in infos) if infos else False
    status = "Solved" if solved else "Attempted"
    lines = [
        f"## Chain {chain_num}: Game24 — {status} ({x})",
        f"<!-- Handles: game24, arithmetic, {x.replace(' ', ', ')}, numbers -->",
    ]
    for i, step_text in enumerate(solutionPath, 1):
        lines.append(f"Thought {i}: {step_text[:120]}")
    return "\n".join(lines)


def ingestTotGame24(source: Path, outFile: Path, limit: int = 0) -> int:
    CATEGORY_DIR.mkdir(parents=True, exist_ok=True)
    traces = json.loads(source.read_text(encoding="utf-8"))
    if limit:
        traces = traces[:limit]
    solved = [t for t in traces if any(i.get("r", 0) == 1 for i in t.get("infos", []))]
    selected = solved if len(solved) >= 5 else traces
    if limit:
        selected = selected[:limit]
    header = (
        "---\n"
        "category: game24\n"
        "keywords: game24, make 24, reach 24, get 24, equals 24, target 24, twenty-four, "
        "four numbers, arithmetic puzzle, number puzzle, numbers operations, calculate 24, "
        "combine numbers, using numbers, use numbers, from numbers, arithmetic, operations\n"
        "---\n\n"
        "# Game24 Reasoning Chains\n\n"
        "Derived from Princeton ToT Game24 benchmark traces (GPT-4 BFS).\n"
    )
    chainBlocks = [b for i, t in enumerate(selected, 1) if (b := _game24Chain(t, i))]
    outFile.write_text(header + "\n\n".join(chainBlocks).rstrip() + "\n", encoding="utf-8")
    logger.info("Wrote %d Game24 chains to %s", len(chainBlocks), outFile)
    return len(chainBlocks)


# ---------------------------------------------------------------------------
# ToT Text
# ---------------------------------------------------------------------------


def ingestTotText(source: Path, outFile: Path, limit: int = 0) -> int:
    CATEGORY_DIR.mkdir(parents=True, exist_ok=True)
    traces = json.loads(source.read_text(encoding="utf-8"))
    selected: list[dict] = []
    seenStarts: set[str] = set()
    for trace in traces:
        steps = trace.get("steps", [])
        if not steps:
            continue
        x = steps[0].get("x", "")
        start = x.split(".")[0].strip().lower()[:30]
        if start not in seenStarts:
            seenStarts.add(start)
            selected.append(trace)
        if len(selected) >= 15:
            break
    if limit:
        selected = selected[:limit]
    header = (
        "---\n"
        "category: creative_writing\n"
        "keywords: write, story, creative, passage, narrative, plan, paragraph, fiction, prose\n"
        "---\n\n"
        "# Creative Writing Reasoning Chains\n\n"
        "Derived from Princeton ToT text coherence benchmark traces (GPT-4).\n"
    )
    chainBlocks = []
    for i, trace in enumerate(selected, 1):
        steps = trace.get("steps", [])
        if not steps:
            continue
        x = steps[0].get("x", "")
        firstSentence = x.split(".")[0].strip()[:60]
        newYs = steps[0].get("new_ys", [])
        if not newYs:
            continue
        plan = newYs[0].strip()[:300].replace("\n", " | ")
        chainBlocks.append(
            f"## Chain {i}: Write a coherent story passage — {firstSentence}\n"
            f"<!-- Handles: write, story, passage, plan, creative, narrative, prose, fiction -->\n"
            f"Thought 1: Story inputs: {firstSentence}\n"
            f"Thought 2: Writing plan: {plan[:120].rstrip()}\n"
            f"Thought 3: Draft a coherent prose passage that incorporates all story inputs.\n"
        )
    outFile.write_text(header + "\n\n".join(chainBlocks).rstrip() + "\n", encoding="utf-8")
    logger.info("Wrote %d creative writing chains to %s", len(chainBlocks), outFile)
    return len(chainBlocks)


class PrincetonToTSource(IngestSource):
    name = "tot-princeton"
    label = "Ingest Princeton ToT"
    help = (
        "Clone/update princeton-nlp/tree-of-thought-llm and ingest all traces "
        "(game24 → data/categories/game24.md, "
        "text → data/categories/creative_writing.md)"
    )

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dest",
            type=Path,
            default=_PRINCETON_TOT_DIR,
            help=f"Local clone destination (default: {_PRINCETON_TOT_DIR})",
        )
        parser.add_argument(
            "--no-update",
            action="store_true",
            help="Skip git pull if repo already cloned",
        )
        parser.add_argument("--limit", type=int, default=0, help="Max traces per file (0=all)")

    def run(self, args: argparse.Namespace) -> list[tuple[str, int, Path]]:
        dest = _ensurePrincetonRepo(args.dest, update=not args.no_update)
        results = []
        for rel_path, kind in _PRINCETON_TRACES:
            src = dest / rel_path
            if not src.exists():
                logger.warning("Trace file not found, skipping: %s", src)
                continue
            if kind == "game24":
                out = CATEGORY_DIR / "game24.md"
                n = ingestTotGame24(src, out, getattr(args, "limit", 0))
                results.append(("Game24", n, out))
            elif kind == "text":
                out = CATEGORY_DIR / "creative_writing.md"
                n = ingestTotText(src, out, getattr(args, "limit", 0))
                results.append(("Creative Writing", n, out))
        return results


# ---------------------------------------------------------------------------
# ArgostranslateSource  — offline translation pack installer
# ---------------------------------------------------------------------------

# Languages and pairs — imported from tinytot.lang (single source of truth)
_TRANSLATE_LANGS = TRANSLATE_LANGS
_TRANSLATE_PAIRS = TRANSLATE_PAIRS


# ---------------------------------------------------------------------------
# OpenTraces — HuggingFace agent trace datasets
# ---------------------------------------------------------------------------

# Map OpenTraces domain classifications to existing TinyToT category names.
# OpenTraces chains are merged into these categories so that routing is
# preserved while the existing categories gain orders of magnitude more data.
_DOMAIN_TO_CATEGORY: dict[str, str] = {
    "python": "programming",
    "java": "programming",
    "javascript": "programming",
    "golang": "programming",
    "rust": "programming",
    "cpp": "programming",
    "algorithms": "computer_science",
    "database": "programming",
    "debugging": "debug",
    "aws": "aws",
    "devops": "aws",
    "web": "programming",
    "planning": "creative_writing",
    "migration": "programming",
}

# OpenTraces datasets config: (hf_repo, label)
_OPENTRACES_DATASETS: list[tuple[str, str]] = [
    ("OpenTraces/lambda-hermes-agent-reasoning-opentraces", "Hermes Agent Reasoning"),
    ("OpenTraces/opentraces-devtime", "DevTime"),
    ("OpenTraces/opentraces-runtime", "Runtime"),
]

_HF_RAW_BASE = "https://huggingface.co/datasets/{repo}/resolve/main/data/{filename}"


def _listOpenTracesFiles(repo: str) -> list[str]:
    """Fetch the list of JSONL filenames from a HuggingFace dataset repo."""
    import requests

    api_url = f"https://huggingface.co/api/datasets/{repo}"
    try:
        resp = requests.get(api_url, timeout=30)
        resp.raise_for_status()
        info = resp.json()
    except Exception as exc:
        logger.warning("Cannot fetch dataset info for %s: %s", repo, exc)
        return []

    siblings = info.get("siblings", [])
    files = []
    for sib in siblings:
        rpath = sib.get("rfilename", "")
        if rpath.startswith("data/") and rpath.endswith(".jsonl"):
            files.append(rpath[len("data/") :])
    return sorted(files)


def _downloadOpenTracesFile(repo: str, filename: str, dest: Path) -> int:
    """Download a single JSONL file from HuggingFace."""
    import requests

    url = _HF_RAW_BASE.format(repo=repo, filename=filename)
    logger.info("Downloading %s ...", url)
    try:
        resp = requests.get(url, timeout=600, stream=True)
        resp.raise_for_status()
        total = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                total += len(chunk)
        logger.info("Downloaded %d bytes to %s", total, dest)
        return total
    except Exception as exc:
        logger.warning("Download failed for %s: %s", url, exc)
        if dest.exists():
            dest.unlink()
        return 0


def _traceToChain(trace: dict, chain_num: int, max_thoughts: int = 10) -> str | None:
    """Convert an OpenTraces TraceRecord into a TinyToT chain block.

    Returns the markdown block string, or None if the trace has no usable
    reasoning content.
    """
    task_desc = trace.get("task", {}).get("description", "") or ""
    steps = trace.get("steps", [])
    outcome = trace.get("outcome", {}) or {}

    if not steps:
        return None

    # Extract reasoning steps from agent/assistant turns
    thoughts: list[str] = []
    for step in steps:
        if step.get("role") in ("agent", "assistant"):
            # Prefer reasoning_content; fall back to content
            text = step.get("reasoning_content") or step.get("content", "") or ""
            text = text.strip()
            if text:
                first_line = text.split("\n")[0].strip()[:200]
                if len(first_line) > 20:
                    thoughts.append(first_line)
        if len(thoughts) >= max_thoughts:
            break

    if not thoughts:
        return None

    # Build handles from task description keywords
    long_words = {w.lower() for w in re.findall(r"\b\w{4,}\b", task_desc)}
    stop_words = {
        "this",
        "that",
        "with",
        "from",
        "have",
        "been",
        "what",
        "will",
        "when",
        "where",
        "which",
        "their",
        "there",
        "about",
        "would",
        "could",
        "should",
        "into",
        "over",
        "such",
        "just",
        "also",
        "than",
        "then",
        "them",
        "some",
        "more",
        "make",
        "need",
        "want",
        "tell",
    }
    handles = sorted(long_words - stop_words)
    handle_str = ", ".join(handles[:8]) if handles else task_desc[:60]

    # Determine outcome as conclusion
    success = outcome.get("success")
    if success is True:
        conclusion = "Task completed successfully."
    elif success is False:
        terminal = outcome.get("terminal_state", "")
        conclusion = f"Task did not complete successfully: {terminal}" if terminal else "Task failed."
    else:
        conclusion = "Task completed with unknown outcome."

    # Build chain title
    title = (task_desc[:80] + "...") if len(task_desc) > 80 else (task_desc or f"OpenTraces Chain {chain_num}")

    lines = [
        f"## Chain {chain_num}: {title}",
        f"<!-- Handles: {handle_str} -->",
    ]
    for i, thought in enumerate(thoughts, 1):
        lines.append(f"Thought {i}: {thought}")
    lines.append(f"Conclusion: {conclusion}")

    return "\n".join(lines)


def _classifyTaskDomain(task_desc: str) -> str:
    """Map a task description to a domain sub-tag for finer-grained categorization.

    Returns a string like 'python', 'java', 'web', 'data', etc.
    """
    lower = task_desc.lower()
    # Language / tech-specific keywords
    if any(w in lower for w in ("python", "pandas", "numpy", "flask", "django", "pytest")):
        return "python"
    if any(w in lower for w in ("java", "spring", "maven", "kotlin")):
        return "java"
    if any(w in lower for w in ("javascript", "typescript", "node", "react", "npm", "js", "ts")):
        return "javascript"
    if any(w in lower for w in ("go ", "golang", "goroutine")):
        return "golang"
    if any(w in lower for w in ("rust", "cargo")):
        return "rust"
    if any(w in lower for w in ("c++", "c ", "cpp", "pointer", "malloc")):
        return "cpp"
    if any(w in lower for w in ("sql", "database", "postgresql", "mysql", "query", "index")):
        return "database"
    if any(w in lower for w in ("aws", "ec2", "s3", "lambda", "cloud")):
        return "aws"
    if any(w in lower for w in ("docker", "kubernetes", "k8s", "container", "deploy")):
        return "devops"
    if any(w in lower for w in ("algorithm", "data structure", "sort", "search", "tree", "graph")):
        return "algorithms"
    if any(w in lower for w in ("test", "debug", "bug", "issue", "error", "fix", "segfault")):
        return "debugging"
    if any(w in lower for w in ("workshop", "plan", "talk", "presentation", "guide", "tutorial")):
        return "planning"
    if any(w in lower for w in ("migrat", "upgrade", "convert", "port", "rewrite")):
        return "migration"
    if any(w in lower for w in ("html", "css", "web", "browser", "extension", "ui")):
        return "web"
    return "general"


def ingestOpenTraces(
    repo: str,
    source_dir_name: str,
    out_dir: Path,
    limit: int = 0,
    max_chains: int = 10000,
    skip_download: bool = False,
) -> dict[str, int]:
    """Download and ingest an OpenTraces dataset, merging chains into existing categories.

    Each trace is classified by domain and its reasoning chain is appended
    to the matching existing TinyToT category .md file.  Traces that do not
    map to any existing category are collected into a separate file.

    Args:
        repo: HuggingFace dataset repo
        source_dir_name: Local subdirectory name under SOURCES_DIR for caching
        out_dir: Output directory for category .md files (typically CATEGORY_DIR)
        limit: Max traces to process (0 = all)
        max_chains: Max chains per target category
        skip_download: If True, use already-cached JSONL files

    Returns: {category_name: chain_count} mapping
    """
    from tinytot.content import getCategories, loadReasoningChains

    source_dir = SOURCES_DIR / source_dir_name
    source_dir.mkdir(parents=True, exist_ok=True)

    # Download JSONL files
    if skip_download:
        jsonl_files = sorted(source_dir.glob("*.jsonl"))
        if not jsonl_files:
            logger.warning("No cached files in %s, falling back to download", source_dir)
            jsonl_files = None
    else:
        jsonl_files = None

    if jsonl_files is None:
        filenames = _listOpenTracesFiles(repo)
        if not filenames:
            logger.error("No JSONL files found for %s", repo)
            return {}

        jsonl_files = []
        for fn in filenames:
            dest = source_dir / fn
            if not dest.exists():
                _downloadOpenTracesFile(repo, fn, dest)
            if dest.exists() and dest.stat().st_size > 0:
                jsonl_files.append(dest)

    if not jsonl_files:
        logger.error("No data downloaded for %s", repo)
        return {}

    # Discover existing categories and their filenames
    existing_cats = getCategories(out_dir)

    # Parse traces, classify domains, group by target category
    cat_chains: dict[str, list[str]] = {}
    general_chains: list[str] = []
    chain_count = 0

    for jf in jsonl_files:
        logger.info("Processing %s ...", jf)
        try:
            with open(jf, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        trace = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    task_desc = trace.get("task", {}).get("description", "") or ""
                    chain = _traceToChain(trace, 0)  # chain num fixed later
                    if chain is None:
                        continue

                    domain = _classifyTaskDomain(task_desc)
                    target_cat = _DOMAIN_TO_CATEGORY.get(domain)
                    if target_cat and target_cat in existing_cats:
                        cat_chains.setdefault(target_cat, []).append(chain)
                    else:
                        general_chains.append(chain)

                    chain_count += 1
                    if limit and chain_count >= limit:
                        break
        except (IOError, OSError) as e:
            logger.warning("Error reading %s: %s", jf, e)

        if limit and chain_count >= limit:
            break

    if not chain_count:
        logger.warning("No chains extracted from %s", repo)
        return {}

    logger.info("Extracted %d chains from %s", chain_count, repo)

    # Write augmentation files: one per target category + one for general/unmapped
    results: dict[str, int] = {}
    target_cats = set(cat_chains.keys()) | {"general"}
    for cat_name in sorted(target_cats):
        if cat_name == "general":
            chains_list = general_chains
            suffix = f"general_{source_dir_name}"
            display_name = f"opentraces_augment_general_{source_dir_name}"
            keywords = "opentraces, agent, reasoning, general, miscellaneous"
            header_desc = f"Uncategorised agent traces from {repo}"
        else:
            chains_list = cat_chains.get(cat_name, [])
            suffix = cat_name
            display_name = f"opentraces_augment_{cat_name}"
            keywords = f"opentraces, {cat_name}, agent, reasoning"
            header_desc = f"OpenTraces {cat_name} augment chains from {repo}"

        if not chains_list:
            continue

        augment_file = out_dir / f"opentraces_augment_{suffix}.md"

        # Append to existing augment file or create new one
        if augment_file.exists():
            # Clear cache so we see the latest chains
            loadReasoningChains.cache_clear()
            existing_content = augment_file.read_text(encoding="utf-8")
            existing_chains = loadReasoningChains(f"opentraces_augment_{suffix}.md", out_dir)
            start_num = len(existing_chains) + 1
        else:
            existing_content = ""
            header_lines = [
                "---",
                f"category: {display_name}",
                f"keywords: {keywords}",
                "---",
                "",
                f"# OpenTraces Augment — {cat_name.title()}",
                "",
                header_desc,
                "",
            ]
            existing_content = "\n".join(header_lines) + "\n"
            start_num = 1

        blocks = []
        for i, ct in enumerate(chains_list[:max_chains]):
            fixed = re.sub(r"^## Chain \d*:?", f"## Chain {start_num + i}:", ct, count=1)
            blocks.append(fixed)
        # Ensure trailing newline before appending
        if not existing_content.endswith("\n"):
            existing_content += "\n"
        augment_file.write_text(existing_content + "\n\n".join(blocks) + "\n", encoding="utf-8")
        results[display_name] = len(blocks)
        logger.info("Wrote %d chains to %s (total: %d)", len(blocks), augment_file, start_num + len(blocks) - 1)

    return results


class OpenTracesSource(IngestSource):
    name = "opentraces"
    label = "Ingest OpenTraces"
    help = (
        "Download and ingest OpenTraces agent reasoning traces from HuggingFace "
        "(lambda-hermes-agent-reasoning-opentraces, opentraces-devtime, opentraces-runtime) "
        "into existing TinyToT categories. Each trace is classified by domain and its "
        "reasoning chain is appended to the matching category (e.g. python -> programming, "
        "debugging -> debug, aws -> aws). Traces that do not map to an existing category "
        "are written to a separate opentraces_general_* file."
    )

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--repo",
            type=str,
            default=None,
            help="Specific dataset repo to ingest (default: all). "
            "e.g. 'OpenTraces/lambda-hermes-agent-reasoning-opentraces'",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max traces to process per dataset (0=all)",
        )
        parser.add_argument(
            "--max-chains",
            type=int,
            default=10000,
            help="Max chains to append per target category (default: 10000)",
        )
        parser.add_argument(
            "--skip-download",
            action="store_true",
            help="Skip download; use already-cached JSONL files",
        )

    def run(self, args: argparse.Namespace) -> list[tuple[str, int, Path]]:
        # Clear caches so getCategories picks up any recently written/deleted files
        from tinytot.content import getCategories, loadReasoningChains
        from tinytot.retrieval import buildChainIndex, buildChainMeta

        getCategories.cache_clear()
        loadReasoningChains.cache_clear()
        buildChainIndex.cache_clear()
        buildChainMeta.cache_clear()

        results = []
        datasets = _OPENTRACES_DATASETS

        if args.repo:
            datasets = [d for d in datasets if d[0] == args.repo]
            if not datasets:
                logger.error("Unknown repo: %s. Available: %s", args.repo, [d[0] for d in _OPENTRACES_DATASETS])
                return results

        for repo, label in datasets:
            source_dir_name = repo.split("/")[-1].replace("-", "_")
            cat_counts = ingestOpenTraces(
                repo=repo,
                source_dir_name=source_dir_name,
                out_dir=CATEGORY_DIR,
                limit=args.limit,
                max_chains=args.max_chains,
                skip_download=args.skip_download,
            )
            if cat_counts:
                for cat_name, count in sorted(cat_counts.items()):
                    cat_file = CATEGORY_DIR / f"{cat_name}.md"
                    results.append((f"{label} -> {cat_name}", count, cat_file))

        # Clear caches so new chains are picked up
        from tinytot.content import getCategories, loadReasoningChains
        from tinytot.retrieval import buildChainIndex, buildChainMeta

        getCategories.cache_clear()
        loadReasoningChains.cache_clear()
        buildChainIndex.cache_clear()
        buildChainMeta.cache_clear()

        return results


# ---------------------------------------------------------------------------
# CS Chain Generator — fills coverage gaps with curated algorithm/DS/system-design chains
# ---------------------------------------------------------------------------

_CS_CHAIN_TEMPLATES: list[dict] = [
    # -- sorting --
    {
        "title": "QuickSort Algorithm — partition-based divide and conquer",
        "handles": "quicksort, sort, partition, divide and conquer, algorithm, pivot, recursion",
        "thoughts": [
            "QuickSort is a divide-and-conquer sorting algorithm that picks a pivot element and partitions the array around it.",
            "Choose a pivot (commonly last element, random element, or median-of-three). Rearrange so elements smaller than pivot go left, larger go right.",
            "Recursively apply the same process to the left and right sub-arrays. Base case: sub-array of size 0 or 1 is already sorted.",
            "Average-case time complexity is O(n log n), worst-case O(n²) when pivot is always the smallest or largest element. Space complexity is O(log n) for the recursion stack.",
        ],
        "conclusion": "QuickSort is an in-place, cache-friendly sorting algorithm with O(n log n) average time. Its worst-case O(n²) can be mitigated with random pivot selection or introspective hybrid approaches.",
    },
    {
        "title": "MergeSort Algorithm — stable divide-and-conquer sorting",
        "handles": "mergesort, sort, divide and conquer, merge, recursion, stable sort, algorithm",
        "thoughts": [
            "MergeSort divides the unsorted list into n sub-lists, each containing one element (a list of one element is trivially sorted).",
            "Repeatedly merge sub-lists to produce new sorted sub-lists until there is only one sub-list remaining (the sorted list).",
            "The merge operation takes two sorted lists and combines them in O(n) time by repeatedly comparing the front elements.",
            "Time complexity is O(n log n) in all cases (best, average, worst). Space complexity is O(n) for the auxiliary array. MergeSort is a stable sort.",
        ],
        "conclusion": "MergeSort guarantees O(n log n) performance in all cases and is stable, making it ideal for sorting linked lists and external sorting where sequential access patterns matter.",
    },
    {
        "title": "HeapSort Algorithm — comparison-based sort using a binary heap",
        "handles": "heapsort, sort, heap, binary heap, priority queue, algorithm, in-place",
        "thoughts": [
            "HeapSort uses a binary heap data structure. First, build a max-heap from the input array in O(n) time using Floyd's heapify algorithm.",
            "Repeatedly extract the maximum element (root of the heap) by swapping it with the last element and reducing heap size. Then sift-down the new root to restore the heap property.",
            "Each extraction takes O(log n) time, and we perform n extractions, giving O(n log n) total. Space complexity is O(1) as it sorts in-place.",
            "HeapSort is not stable — equivalent elements may be reordered. It has good worst-case guarantees but worse cache performance than QuickSort.",
        ],
        "conclusion": "HeapSort provides O(n log n) worst-case time with O(1) additional space. Its in-place nature and deterministic performance make it useful for systems with strict latency requirements.",
    },
    {
        "title": "Radix Sort — non-comparison integer sorting by digit",
        "handles": "radix sort, sort, non-comparison, digit, counting sort, stable, linear time",
        "thoughts": [
            "Radix Sort processes integer keys digit by digit, from least significant to most significant (LSD) or vice versa (MSD). It uses a stable sub-sort (counting sort) for each digit.",
            "For base-b digits, sort each digit position using counting sort: count occurrences, compute prefix sums, then place elements in correct positions in O(n + b) time per digit.",
            "With d digits and base b, total time is O(d(n + b)). For fixed-width integers (32-bit, 64-bit), d is constant, making Radix Sort O(n) — faster than comparison sorts for large n.",
            "Space complexity is O(n + b) for the auxiliary array and digit buckets. Radix Sort only works for integer or fixed-length key types.",
        ],
        "conclusion": "Radix Sort achieves linear O(n) time for fixed-width integer keys, beating comparison sorts for large datasets. It trades generality for raw speed.",
    },
    {
        "title": "Binary Search — efficient search on sorted arrays",
        "handles": "binary search, search, sorted array, divide and conquer, algorithm, O(log n)",
        "thoughts": [
            "Binary search finds a target value in a sorted array by repeatedly dividing the search interval in half.",
            "Compare the target with the middle element. If equal, return the index. If target < middle, search the left half; otherwise search the right half.",
            "Each comparison eliminates half of the remaining elements, giving O(log n) time complexity. Requires the array to be sorted upfront (O(n log n) to sort).",
            "Variants include finding the first/last occurrence of a duplicate, searching in rotated arrays, and exponential search for unbounded arrays.",
        ],
        "conclusion": "Binary search is the canonical O(log n) search algorithm for sorted data. It is a fundamental building block used in everything from database indexing to debugging (git bisect).",
    },
    # -- graph --
    {
        "title": "Dijkstra's Algorithm — single-source shortest paths on weighted graphs",
        "handles": "dijkstra, shortest path, graph, weighted, algorithm, priority queue, greedy",
        "thoughts": [
            "Dijkstra's algorithm finds the shortest paths from a source node to all other nodes in a weighted graph with non-negative edge weights.",
            "Initialize distances: source=0, all others=infinity. Use a min-priority queue (binary heap) keyed by current distance. Extract the node with minimum distance.",
            "For each neighbor, calculate the new distance = current_node_distance + edge_weight. If this is less than the recorded distance, update and push to the priority queue.",
            "Time complexity is O((V + E) log V) with a binary heap, or O(V²) with an array. Dijkstra fails on negative edge weights — use Bellman-Ford instead.",
        ],
        "conclusion": "Dijkstra's algorithm is the foundation of most real-world shortest-path routing (GPS navigation, network routing protocols like OSPF and IS-IS). It greedily selects the closest unvisited node.",
    },
    {
        "title": "A* Search — heuristic-guided pathfinding on graphs",
        "handles": "a-star, A*, pathfinding, heuristic, graph, search, algorithm, admissible",
        "thoughts": [
            "A* extends Dijkstra's algorithm with a heuristic function h(n) that estimates the cost from node n to the goal. The evaluation function is f(n) = g(n) + h(n), where g(n) is the known cost from the start.",
            "A* maintains an open set (frontier) and a closed set (visited). At each step, expand the node with the lowest f(n). If h(n) is admissible (never overestimates), A* guarantees the optimal path.",
            "Common heuristics: Euclidean distance (straight-line), Manhattan distance (grid-based movement), and octile distance (8-directional movement).",
            "A* is widely used in video games for NPC pathfinding, robotics motion planning, and puzzle solving. Its efficiency depends on the quality of the heuristic.",
        ],
        "conclusion": "A* combines the completeness of Dijkstra with heuristic-guided search, making it the go-to algorithm for optimal pathfinding in games, robotics, and navigation.",
    },
    {
        "title": "Topological Sort — linear ordering of DAG vertices",
        "handles": "topological sort, DAG, graph, dependency, ordering, Kahn, DFS",
        "thoughts": [
            "Topological sort produces a linear ordering of vertices in a Directed Acyclic Graph (DAG) such that for every directed edge u->v, u comes before v in the ordering.",
            "Kahn's algorithm (BFS-based): compute in-degree of each vertex. Add vertices with in-degree 0 to a queue. While queue not empty, remove a vertex, decrement in-degrees of its neighbors, add newly zeroed vertices.",
            "DFS-based approach: run DFS and add each vertex to the ordering after all its descendants have been visited (post-order). Reverse the result for the topological order.",
            "Applications include build systems (Makefile), dependency resolution (pip/npm), task scheduling, and course prerequisite planning.",
        ],
        "conclusion": "Topological sort enables dependency resolution and task ordering. Kahn's algorithm with in-degree tracking handles cycle detection naturally and runs in O(V + E) time.",
    },
    {
        "title": "Bellman-Ford Algorithm — shortest paths handling negative edges",
        "handles": "bellman-ford, shortest path, negative edge, graph, algorithm, dynamic programming",
        "thoughts": [
            "Bellman-Ford computes shortest paths from a single source, handling negative edge weights. It can also detect negative-weight cycles reachable from the source.",
            "Initialize distances to infinity, source to 0. Relax all edges V-1 times: for each edge (u, v, w), if dist[u] + w < dist[v], update dist[v].",
            "After V-1 relaxations, run one more pass. If any distance still decreases, a negative-weight cycle exists and no shortest path is defined.",
            "Time complexity is O(VE), slower than Dijkstra but more general. Used in distance-vector routing protocols (RIP) and for detecting negative cycles in financial arbitrage detection.",
        ],
        "conclusion": "Bellman-Ford trades raw speed (O(VE)) for the ability to handle negative edge weights and detect negative cycles — essential capabilities that Dijkstra cannot provide.",
    },
    # -- DP --
    {
        "title": "0/1 Knapsack — dynamic programming for constrained optimization",
        "handles": "knapsack, dynamic programming, optimization, DP, subset, combinatorial",
        "thoughts": [
            "Given n items each with weight w[i] and value v[i], choose a subset to maximize total value within capacity W. Each item can be taken at most once (0/1 property).",
            "Define dp[i][c] = max value using first i items with capacity c. Recurrence: dp[i][c] = max(dp[i-1][c], dp[i-1][c-w[i]] + v[i]) if w[i] <= c, else dp[i-1][c].",
            "Time complexity is O(nW) — pseudo-polynomial. Space can be optimized to O(W) using a 1D array iterated in reverse to prevent reusing items.",
            "Variants include unbounded knapsack (items reusable), fractional knapsack (greedy, solvable with sort by value/weight ratio), and multi-dimensional knapsack.",
        ],
        "conclusion": "The 0/1 knapsack DP is the quintessential combinatorial optimization problem. Its recurrence pattern (take or skip) generalizes to resource allocation, portfolio selection, and project planning.",
    },
    {
        "title": "Longest Common Subsequence — sequence comparison via DP",
        "handles": "LCS, longest common subsequence, DP, string, sequence, comparison, diff",
        "thoughts": [
            "LCS finds the longest subsequence common to two sequences. A subsequence appears in the same order but not necessarily contiguously.",
            "Define dp[i][j] = LCS length for prefixes of length i and j. If chars match: dp[i][j] = dp[i-1][j-1] + 1. Otherwise: dp[i][j] = max(dp[i-1][j], dp[i][j-1]).",
            "Time and space are O(mn). Space can be reduced to O(min(m,n)) using only two rows. Backtracking through the DP table reconstructs the actual subsequence.",
            "Applications include diff/patch tools, DNA sequence alignment (Smith-Waterman), version control, and plagiarism detection.",
        ],
        "conclusion": "LCS is the core of sequence comparison algorithms. Its DP formulation generalizes to edit distance, sequence alignment, and computational biology applications.",
    },
    {
        "title": "Edit Distance (Levenshtein) — minimum edit operations between strings",
        "handles": "edit distance, levenshtein, DP, string, transformation, spell check, alignment",
        "thoughts": [
            "Edit distance measures the minimum number of single-character operations (insert, delete, substitute) needed to transform one string into another.",
            "Define dp[i][j] = edit distance for prefixes of length i and j. Base: dp[i][0] = i (i deletions), dp[0][j] = j (j insertions). Recurrence: if chars match, dp[i-1][j-1]; else 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]).",
            "Time O(mn), space O(mn) or O(min(m,n)) with space optimization. The substitution operation can have different costs for different character pairs.",
            "Used in spell checkers (suggest corrections), DNA sequence analysis, natural language processing, and duplicate detection.",
        ],
        "conclusion": "Edit distance provides a fundamental measure of string similarity with O(mn) DP. It is the basis for fuzzy string matching, autocorrect, and bioinformatics alignment.",
    },
    # -- system design --
    {
        "title": "Design a Weighted Round-Robin Load Balancer — algorithm and implementation",
        "handles": "load balancer, round robin, weighted, algorithm, design, system design, distribution, capacity, server, traffic, nginx, scheduling",
        "thoughts": [
            "To design a weighted round-robin load balancer algorithm: each backend server is assigned a capacity weight. A server with weight 3 receives 3x the traffic of a server with weight 1. The algorithm distributes requests in proportion to these weights.",
            "Basic implementation: maintain an array of server weights and a running index counter. Keep a current_weight variable. At each request, iterate servers. Subtract 1 from each server's remaining weight, send request to the first server whose remaining weight reaches 0 first. Reset when all weights are exhausted.",
            "Smooth Weighted Round-Robin (Nginx algorithm) eliminates burstiness: maintain each server's current weight initialized to its configured weight. At each selection step, add the configured weight to each server's current weight, pick the server with highest current weight, then subtract the total sum of all configured weights from it. This spreads requests evenly over time.",
            "Time complexity is O(1) per request using pre-computed greatest common divisor (GCD) of all weights. The space complexity is O(N) for N servers. This design is used by Nginx, HAProxy, and cloud load balancers (AWS ALB, GCP HTTP LB) for weighted traffic distribution.",
        ],
        "conclusion": "A weighted round-robin load balancer design uses per-server capacity weights to proportionally distribute incoming traffic. Nginx's smooth variant provides burst-free distribution, making it suitable for production traffic management in microservices architectures.",
    },
    {
        "title": "Consistent Hashing — distributed key distribution with minimal remapping",
        "handles": "consistent hashing, distributed, hash ring, partitioning, scalability, sharding",
        "thoughts": [
            "Consistent hashing maps both keys and server nodes onto a circular hash ring (0 to 2^m - 1). Each key is assigned to the next server encountered when moving clockwise from the key's hash position.",
            "When a server is added or removed, only the keys between that server and its predecessor need to be remapped — not all keys. This is O(K/N) remapping instead of O(K) with naive modulo hashing.",
            "Virtual nodes (replicas) improve load distribution: each physical server appears as multiple virtual nodes at different positions on the ring, preventing hot spots when servers have different capacities.",
            "Used by Amazon DynamoDB, Cassandra, Discord, and CDNs. Consistent hashing enables elastic scalability with minimal data movement during cluster changes.",
        ],
        "conclusion": "Consistent hashing solves the distributed rebalancing problem: adding or removing a node only affects O(1/N) of keys, making it the foundation of modern distributed key-value stores.",
    },
    {
        "title": "Rate Limiting Algorithm — Token Bucket for traffic shaping",
        "handles": "rate limiting, token bucket, algorithm, traffic shaping, throttling, leaky bucket",
        "thoughts": [
            "The Token Bucket algorithm maintains a bucket of tokens that fills at a constant rate (refill_rate tokens per second). Each request consumes one token. If the bucket is empty, the request is rejected or queued.",
            "The bucket has a maximum capacity (burst_size) allowing short bursts of traffic up to that limit. Over time, the sustained rate is bounded by the refill rate.",
            "Implementation: store last_refill_timestamp and token_count. On each request, calculate elapsed time, add refill_rate * elapsed tokens (capped at burst_size), then decrement if tokens available.",
            "Sliding Window Log (more precise) stores timestamps of all requests in the current window. Sliding Window Counter (memory-efficient) uses the previous window count plus partial current window.",
        ],
        "conclusion": "Token Bucket is the most widely used rate-limiting algorithm, balancing average throughput and burst allowance. It is simple, space-efficient, and supported by virtually all API gateways.",
    },
    {
        "title": "Raft Consensus Algorithm — replicated state machine for fault tolerance",
        "handles": "raft, consensus, distributed, replication, fault tolerance, leader election, log",
        "thoughts": [
            "Raft manages a replicated log across a cluster of servers. It elects a leader that clients communicate with. The leader accepts log entries, replicates them to followers, and commits them on majority acknowledgement.",
            "Leader election: servers start as followers. If no leader heartbeat received within election timeout (150-300ms randomized), candidate increments term, requests votes from peers. Server with majority votes becomes leader for that term.",
            "Log replication: leader appends entry to local log, sends AppendEntries RPCs to followers. Entry is committed when leader receives confirmation from majority. Leader maintains nextIndex and matchIndex per follower.",
            "Safety: the leader always has the most complete log. A candidate cannot become leader unless its log is at least as up-to-date as a majority. Raft ensures exactly-once semantics through log compaction and snapshotting.",
        ],
        "conclusion": "Raft was designed specifically for understandability and is the consensus engine behind etcd, Consul, and many distributed databases, ensuring linearizable consistency across node failures.",
    },
    # -- concurrency --
    {
        "title": "Producer-Consumer Pattern — thread-safe bounded buffer with condition variables",
        "handles": "producer consumer, thread safety, bounded buffer, condition variable, mutex, synchronization",
        "thoughts": [
            "The producer-consumer pattern decouples data production from consumption using a shared bounded buffer. Producers add items, consumers remove them, and the buffer size limits memory usage.",
            "Use a mutex to protect the buffer and two condition variables: not_full (signaled when space becomes available) and not_empty (signaled when data becomes available).",
            "Producer: lock mutex, wait on not_full if buffer is full, add item, unlock, signal not_empty. Consumer: lock mutex, wait on not_empty if buffer is empty, remove item, unlock, signal not_full.",
            "In Python, use threading.Lock with threading.Condition, or queue.Queue for a ready-made implementation. In Go, use channels. In Java, use BlockingQueue implementations.",
        ],
        "conclusion": "The producer-consumer pattern with condition variables is the canonical concurrent programming pattern. It demonstrates thread-safe communication, blocking synchronization, and bounded resource management.",
    },
    {
        "title": "Deadlock Prevention — four necessary conditions and avoidance strategies",
        "handles": "deadlock, prevention, mutex, hold and wait, circular wait, no preemption, dining philosophers",
        "thoughts": [
            "Deadlock requires four conditions: Mutual Exclusion (resources cannot be shared), Hold and Wait (thread holds resources while waiting for others), No Preemption (resources cannot be forcibly taken), Circular Wait (a cycle of threads each waiting for the next).",
            "Prevention: eliminate any one condition. Break Hold-and-Wait by acquiring all locks at once (atomic acquisition). Break Circular Wait by enforcing a global lock ordering (all threads acquire locks in the same order).",
            "Avoidance: use Banker's Algorithm where threads declare maximum resource needs in advance. The system checks if granting a request leaves a safe state (some sequence where all threads can complete).",
            "Detection (allow then recover): build a wait-for graph and check for cycles. Recovery options: thread termination, resource preemption, or rollback to a checkpoint.",
        ],
        "conclusion": "Deadlock prevention through lock ordering is the most practical approach. The dining philosophers problem with ordered chopstick pickup demonstrates how a simple ordering rule eliminates circular wait.",
    },
    # -- trees --
    {
        "title": "Binary Search Tree — ordered data structure with O(log n) operations",
        "handles": "binary search tree, BST, tree, data structure, search, insert, delete, balanced",
        "thoughts": [
            "A BST is a binary tree where each node's left subtree contains only values less than the node's key, and the right subtree contains only values greater.",
            "Search: compare target with root. If equal, found. If less, search left subtree. If greater, search right subtree. Time O(h) where h is tree height.",
            "Insert: search for the key. If not found, insert at the leaf position where the search stopped. Delete: three cases — leaf (remove), one child (replace with child), two children (replace with in-order successor).",
            "In a balanced BST, h = O(log n). In the worst case (inserting sorted data), h = O(n) — a degenerate tree. Self-balancing variants (AVL, Red-Black) maintain O(log n) height.",
        ],
        "conclusion": "The BST is a fundamental data structure providing O(log n) search when balanced. Its recursive structure makes it ideal for range queries, order statistics, and as the foundation of more advanced tree structures.",
    },
    {
        "title": "AVL Tree — self-balancing BST with strict height enforcement",
        "handles": "AVL, tree, balanced, BST, rotation, height, data structure, self-balancing",
        "thoughts": [
            "An AVL tree is a self-balancing BST where the heights of left and right subtrees of every node differ by at most 1 (balance factor -1, 0, or +1).",
            "After every insert or delete, walk up toward the root checking balance factors. If imbalance > 1, perform tree rotations: left rotation, right rotation, left-right rotation, or right-left rotation.",
            "Left rotation: node's right child becomes new root, node becomes left child of new root. Right rotation: symmetric. Double rotations combine a left rotation followed by a right rotation (or vice versa).",
            "Height is strictly O(log n). Search is O(log n) worst-case. Insert and delete require O(log n) rotations. More rigidly balanced than Red-Black trees but more rotation overhead.",
        ],
        "conclusion": "AVL trees provide faster lookups than Red-Black trees due to stricter balancing, at the cost of more rotations during writes. Use when reads dominate over writes.",
    },
    {
        "title": "Trie (Prefix Tree) — efficient string search and prefix matching",
        "handles": "trie, prefix tree, string, search, autocomplete, data structure, radix tree",
        "thoughts": [
            "A trie stores strings in a tree where each node represents a character prefix. The root is empty; each path from root to a node spells a prefix. Nodes can be marked as terminal (end of a word).",
            "Insert: walk the tree character by character, creating new nodes where paths do not exist. Mark the final node as terminal. Search: walk the tree character by character; return true only if the final node exists and is terminal.",
            "Space complexity is O(ALPHABET_SIZE * total_characters), which can be large. Compressed tries (radix trees) merge nodes with single children to save space.",
            "Applications: autocomplete suggestions (walk to prefix node, then explore all terminal descendants), spell checking, IP routing (longest prefix match), and dictionary word storage.",
        ],
        "conclusion": "Tries provide O(k) search and insert where k is string length — independent of the number of stored strings. They excel at prefix-based operations like autocomplete and IP routing.",
    },
]


def generateCSChains(out_dir: Path) -> int:
    """Generate curated CS algorithm/DS/system-design chains, appending to augment file."""
    from tinytot.content import loadReasoningChains

    loadReasoningChains.cache_clear()

    augment_file = out_dir / "opentraces_augment_computer_science.md"
    existing = loadReasoningChains("opentraces_augment_computer_science.md")
    start_num = len(existing) + 1

    blocks = []
    for i, tpl in enumerate(_CS_CHAIN_TEMPLATES, start_num):
        lines = [
            f"## Chain {i}: {tpl['title']}",
            f"<!-- Handles: {tpl['handles']} -->",
        ]
        for j, thought in enumerate(tpl["thoughts"], 1):
            lines.append(f"Thought {j}: {thought}")
        lines.append(f"Conclusion: {tpl['conclusion']}")
        blocks.append("\n".join(lines))

    existing_content = augment_file.read_text(encoding="utf-8")
    if not existing_content.endswith("\n"):
        existing_content += "\n"
    augment_file.write_text(existing_content + "\n" + "\n\n".join(blocks) + "\n", encoding="utf-8")

    new_count = len(blocks)
    total = len(existing) + new_count
    logger.info("Generated %d CS chains -> %s (total: %d)", new_count, augment_file, total)
    return new_count


class CSChainGenerator(IngestSource):
    name = "cs-chains"
    label = "Generate CS Chains"
    help = (
        "Generate curated computer science reasoning chains (algorithms, data structures, "
        "system design) to fill coverage gaps in the opentraces_augment_computer_science.md "
        "file.  Appends new chains without removing existing ones."
    )

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, args: argparse.Namespace) -> list[tuple[str, int, Path]]:
        n = generateCSChains(CATEGORY_DIR)
        if n:
            return [("CS Chain Generator", n, CATEGORY_DIR / "opentraces_augment_computer_science.md")]
        return []


class ArgostranslateSource(IngestSource):
    name = "translate-packs"
    label = "Ingest Translation Packs"
    help = (
        "Download argostranslate language packs for offline translation. "
        "Installs pairs for en↔fr/de/es/ko/zh/ja/pt/it/ar/hi/ru by default. "
        "Requires network access once; translation works offline afterwards."
    )

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--pairs",
            nargs="*",
            metavar="SRC-TGT",
            help="Additional pairs to install e.g. --pairs en-nl nl-en (default: install all benchmark pairs)",
        )

    def run(self, args: argparse.Namespace) -> list[tuple[str, int, Path]]:
        try:
            import argostranslate.package
            import argostranslate.translate
        except ImportError:
            logger.error("argostranslate not installed. Run: pip install argostranslate")
            return [("argostranslate", 0, Path("."))]

        pairs = list(_TRANSLATE_PAIRS)
        for extra in getattr(args, "pairs", None) or []:
            parts = extra.split("-", 1)
            if len(parts) == 2:
                pairs.append((parts[0], parts[1]))

        logger.info("Updating argostranslate package index...")
        try:
            argostranslate.package.update_package_index()
        except Exception as e:
            logger.warning("Package index update failed: %s", e)
            return [("argostranslate", 0, Path("."))]

        available = argostranslate.package.get_available_packages()
        installedCount = 0
        skippedCount = 0

        # Check what's already installed
        installedLangs = argostranslate.translate.get_installed_languages()
        installedPairs = {
            (src.code, tgt.code) for src in installedLangs for tgt in src.translations_to if getattr(tgt, "code", None)
        }

        for srcCode, tgtCode in pairs:
            if (srcCode, tgtCode) in installedPairs:
                skippedCount += 1
                continue
            pkg = next(
                (p for p in available if p.from_code == srcCode and p.to_code == tgtCode),
                None,
            )
            if pkg:
                try:
                    logger.info("Installing %s→%s pack...", srcCode, tgtCode)
                    argostranslate.package.install_from_path(pkg.download())
                    installedCount += 1
                except Exception as e:
                    logger.warning("Failed to install %s→%s: %s", srcCode, tgtCode, e)
            else:
                logger.warning("No pack available for %s→%s", srcCode, tgtCode)

        msg = f"Installed {installedCount} packs, {skippedCount} already present"
        logger.info(msg)
        return [("argostranslate packs", installedCount + skippedCount, Path("."))]


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------

_SOURCES: list[type[IngestSource]] = [
    GSM8KSource,
    PrincetonToTSource,
    OpenTracesSource,
    CSChainGenerator,
    ArgostranslateSource,
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Ingest trace corpora into TinyToT")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Register each source as a subcommand
    for src_cls in _SOURCES:
        p = sub.add_parser(src_cls.name, help=src_cls.help)
        src_cls.add_args(p)

    # 'all' runs every source with its defaults
    p_all = sub.add_parser("all", help="Run all ingest sources")
    p_all.add_argument("--no-update", action="store_true", help="Skip git pull for remote sources")
    p_all.add_argument("--limit", type=int, default=0)

    args = parser.parse_args()

    if args.cmd == "all":
        for src_cls in _SOURCES:
            # Synthesise a minimal namespace with defaults for each source
            defaults = argparse.Namespace(limit=args.limit, no_update=args.no_update)
            for action in sub._name_parser_map[src_cls.name]._actions:
                if action.dest not in vars(defaults) and action.default is not None:
                    setattr(defaults, action.dest, action.default)
            _runSource(src_cls(), defaults)
    else:
        src = next(s() for s in _SOURCES if s.name == args.cmd)
        _runSource(src, args)

    print("\nIngestion complete. Restart the server to rebuild indexes.")


def _runSource(src: IngestSource, args: argparse.Namespace) -> None:
    from tinytot.benchmark import _print_section

    _print_section(src.label or src.name)
    try:
        for label, count, out in src.run(args):
            print(f"  {label}: {count} entries -> {out}")
    except Exception as exc:
        logger.error("%s failed: %s", src.name, exc)


if __name__ == "__main__":
    main()
