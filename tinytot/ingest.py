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
            print(f"  {label}: {count} entries → {out}")
    except Exception as exc:
        logger.error("%s failed: %s", src.name, exc)


if __name__ == "__main__":
    main()
