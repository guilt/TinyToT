"""tinytot.parity — compare reasoning traces across opencode providers/models.

Consumes opencode session exports (JSON produced by ``opencode export``) and
computes three parity views, motivated by the "Stolen Thoughts" paper
(https://stolen-thoughts.com/paper.pdf):

  extraction-fidelity
      Per-step ratio of extracted reasoning tokens (from the ``reasoning`` part
      text) to the API-reported ``tokens.reasoning`` count — the paper's
      faithfulness metric.  Steps whose reasoning is an opaque/encrypted block
      (reported > 0, extracted == 0) are surfaced and inventoried separately;
      no decoding is attempted.

  cross-provider
      Groups sessions by identical task, then compares reasoning length, step
      count, extraction fidelity, and token-set overlap across providers and
      models to surface divergence.

  routing
      Runs each task through TinyToT's actual dispatch (``detectResponseMode``
      + ``categorizePrompt``) and reports agreement with the category expected
      from the task description, guarding against routing regressions.

Usage
-----
    tinytot-parity data/.sources/opencode fidelity
    tinytot-parity data/.sources/opencode cross
    tinytot-parity data/.sources/opencode routing
    tinytot-parity data/.sources/opencode all --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from tinytot._stdio import ensureUtf8Stdio
from tinytot.content import CATEGORY_DIR, DATA_DIR
from tinytot.ingest import (
    _DOMAIN_TO_CATEGORY,
    _classifyTaskDomain,
    _opencodeSessionInfo,
    _opencodeSteps,
    _opencodeTask,
)

# Word-token estimate, consistent with the codebase's chain token metric.
_TOKEN_RE = re.compile(r"\b\w{3,}\b")


# ---------------------------------------------------------------------------
# Trace model
# ---------------------------------------------------------------------------


@dataclass
class TraceStep:
    reasoning: str
    output: str
    tokens: dict
    cost: float
    model: str
    provider: str
    reasoning_meta: dict = field(default_factory=dict)


@dataclass
class Trace:
    session_id: str
    task: str
    provider: str
    model: str
    steps: list[TraceStep] = field(default_factory=list)
    tokens: dict = field(default_factory=dict)
    cost: float = 0.0


def parseExport(export: dict) -> Trace:
    """Parse a single opencode session export dict into a Trace."""
    info = _opencodeSessionInfo(export)
    model = info.get("model") or {}
    steps = [
        TraceStep(
            reasoning=s.get("reasoning", ""),
            output=s.get("output", ""),
            tokens=s.get("tokens") or {},
            cost=s.get("cost", 0),
            model=s.get("model", ""),
            provider=s.get("provider", ""),
            reasoning_meta=s.get("reasoning_meta") or {},
        )
        for s in _opencodeSteps(export)
    ]
    return Trace(
        session_id=info.get("id", ""),
        task=_opencodeTask(export),
        provider=model.get("providerID", ""),
        model=model.get("id", ""),
        steps=steps,
        tokens=info.get("tokens") or {},
        cost=info.get("cost", 0),
    )


def parseExports(export_dir: Path) -> list[Trace]:
    """Parse every ``*.json`` export under export_dir into a list of Traces."""
    from tinytot.ingest import _iterOpenCodeExports

    return [parseExport(e) for e in _iterOpenCodeExports(export_dir)]


# ---------------------------------------------------------------------------
# Shared metrics
# ---------------------------------------------------------------------------


def extractedTokens(text: str) -> int:
    """Estimate reasoning tokens from plaintext using the word-token metric."""
    return len(_TOKEN_RE.findall(text.lower()))


def taskKey(task: str) -> str:
    """Normalise a task string so identical prompts group across models."""
    norm = re.sub(r"\s+", " ", task.strip().lower())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def modelFamily(model: str) -> str:
    """Map a model id to its underlying vendor family.

    opencode routes all providers through the ``opencode`` gateway, so the
    export's ``providerID`` does not identify the vendor.  The model id does:
    ``claude-*`` → anthropic, ``gpt-*`` → openai, ``gemini-*`` → google,
    ``grok-*`` → xai, ``deepseek-*`` → deepseek.
    """
    m = model.lower()
    for family, prefixes in (
        ("anthropic", ("claude", "opus", "sonnet", "haiku")),
        ("openai", ("gpt", "o1", "o3", "o4")),
        ("google", ("gemini", "palm")),
        ("xai", ("grok",)),
        ("deepseek", ("deepseek",)),
        ("qwen", ("qwen",)),
        ("kimi", ("kimi",)),
        ("glm", ("glm",)),
        ("mistral", ("mistral",)),
        ("meta", ("llama",)),
    ):
        if any(m.startswith(p) for p in prefixes):
            return family
    return "other"


def encryptedBlocks(step: TraceStep) -> list[dict]:
    """Inventory encrypted reasoning blocks embedded in a step's metadata.

    The "Stolen Thoughts" paper (https://stolen-thoughts.com/paper.pdf)
    describes provider reasoning shipped to clients as encrypted blocks.
    opencode's export surfaces these as ``reasoningEncryptedContent`` in the
    reasoning part metadata.  This extracts them for inventory only — no
    decoding is attempted.
    """
    blocks: list[dict] = []
    for vendor, payload in (step.reasoning_meta or {}).items():
        if not isinstance(payload, dict):
            continue
        content = payload.get("reasoningEncryptedContent")
        if content:
            blocks.append(
                {
                    "vendor": vendor,
                    "item_id": payload.get("itemId", ""),
                    "block_chars": len(content),
                    "has_summary": bool(step.reasoning.strip()),
                }
            )
    return blocks


def stepFidelity(step: TraceStep) -> tuple[Optional[float], bool]:
    """Return (fidelity, opaque) for one step.

    fidelity = extracted_reasoning_tokens / reported_reasoning_tokens
    Returns None when no reasoning tokens were reported (the paper's ground
    truth is the API-reported thinking-token count, so the ratio is undefined
    without it).  ``opaque`` is True when tokens were reported but no reasoning
    text could be extracted (e.g. an encrypted thinking block) — the paper's
    attack surface, surfaced here for inventory only.
    """
    reported = int(step.tokens.get("reasoning", 0) or 0)
    extracted = extractedTokens(step.reasoning)
    if reported <= 0:
        return (None, False)
    return (extracted / reported, extracted == 0)


# ---------------------------------------------------------------------------
# Extraction fidelity
# ---------------------------------------------------------------------------


def fidelityReport(traces: list[Trace]) -> dict:
    """Compute per-step and per-session extraction fidelity."""
    per_step = []
    opaque: list[dict] = []
    blocks: list[dict] = []
    for tr in traces:
        for i, step in enumerate(tr.steps):
            fidelity, is_opaque = stepFidelity(step)
            reported = int(step.tokens.get("reasoning", 0) or 0)
            extracted = extractedTokens(step.reasoning)
            row = {
                "session": tr.session_id,
                "provider": step.provider or tr.provider,
                "model": step.model or tr.model,
                "family": modelFamily(step.model or tr.model),
                "step": i + 1,
                "reported": reported,
                "extracted": extracted,
                "fidelity": fidelity,
                "opaque": is_opaque,
                "unreported": reported <= 0 and extracted > 0,
            }
            per_step.append(row)
            if is_opaque:
                opaque.append(
                    {
                        "session": tr.session_id,
                        "provider": step.provider or tr.provider,
                        "model": step.model or tr.model,
                        "family": modelFamily(step.model or tr.model),
                        "step": i + 1,
                        "reported_tokens": reported,
                    }
                )
            for b in encryptedBlocks(step):
                blocks.append(
                    {
                        "session": tr.session_id,
                        "provider": step.provider or tr.provider,
                        "model": step.model or tr.model,
                        "family": modelFamily(step.model or tr.model),
                        "step": i + 1,
                        **b,
                    }
                )

    ratios = [s["fidelity"] for s in per_step if s["fidelity"] is not None]
    by_family: dict[str, dict] = {}
    for s in per_step:
        if s["fidelity"] is None:
            continue
        p = by_family.setdefault(s["family"], {"count": 0, "fidelities": []})
        p["count"] += 1
        p["fidelities"].append(s["fidelity"])
    family_summary = {
        p: {"steps": v["count"], "mean_fidelity": round(sum(v["fidelities"]) / len(v["fidelities"]), 3)}
        for p, v in by_family.items()
    }
    return {
        "steps": per_step,
        "opaque_blocks": opaque,
        "encrypted_blocks": blocks,
        "family_fidelity": family_summary,
        "summary": {
            "steps_with_reported": len(ratios),
            "mean_fidelity": round(sum(ratios) / len(ratios), 3) if ratios else None,
            "opaque_count": len(opaque),
            "encrypted_block_count": len(blocks),
            "unreported_reasoning_steps": sum(1 for s in per_step if s["unreported"]),
            "total_reported_reasoning_tokens": sum(s["reported"] for s in per_step),
            "total_extracted_reasoning_tokens": sum(s["extracted"] for s in per_step),
        },
    }


# ---------------------------------------------------------------------------
# Cross-provider parity
# ---------------------------------------------------------------------------


def _jaccard(a: set, b: set) -> Optional[float]:
    if not a and not b:
        return None
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def crossProviderReport(traces: list[Trace]) -> dict:
    """Group traces by task and compare reasoning across models/providers."""
    groups: dict[str, list[Trace]] = {}
    for tr in traces:
        if tr.steps:
            groups.setdefault(taskKey(tr.task), []).append(tr)

    tasks: list[dict] = []
    for key, members in groups.items():
        members.sort(key=lambda t: (modelFamily(t.model), t.model))
        rows = []
        for tr in members:
            reported = sum(int(s.tokens.get("reasoning", 0) or 0) for s in tr.steps)
            extracted = sum(extractedTokens(s.reasoning) for s in tr.steps)
            ratios = [f for f, _ in (stepFidelity(s) for s in tr.steps) if f is not None]
            rows.append(
                {
                    "provider": tr.provider,
                    "model": tr.model,
                    "family": modelFamily(tr.model),
                    "session": tr.session_id,
                    "steps": len(tr.steps),
                    "reported_tokens": reported,
                    "extracted_tokens": extracted,
                    "fidelity": round(sum(ratios) / len(ratios), 3) if ratios else None,
                    "output_chars": sum(len(s.output) for s in tr.steps),
                }
            )

        pairs = []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                ta = " ".join(s.reasoning for s in members[i].steps)
                tb = " ".join(s.reasoning for s in members[j].steps)
                jaccard = _jaccard(set(_TOKEN_RE.findall(ta.lower())), set(_TOKEN_RE.findall(tb.lower())))
                pairs.append(
                    {
                        "a": f"{modelFamily(members[i].model)}/{members[i].model}",
                        "b": f"{modelFamily(members[j].model)}/{members[j].model}",
                        "reasoning_jaccard": round(jaccard, 3) if jaccard is not None else None,
                    }
                )

        tasks.append(
            {
                "task": members[0].task,
                "task_key": key,
                "models": rows,
                "pairs": pairs,
            }
        )

    return {"tasks": tasks}


# ---------------------------------------------------------------------------
# Routing parity
# ---------------------------------------------------------------------------


def routingReport(traces: list[Trace], category_dir: Path = CATEGORY_DIR) -> dict:
    """Run each task through TinyToT dispatch and check expected category."""
    from tinytot.inference import detectResponseMode, generateReasoningResponse
    from tinytot.retrieval import categorizePrompt

    rows = []
    for tr in traces:
        if not tr.task:
            continue
        task = tr.task
        mode = detectResponseMode(task)
        routed = categorizePrompt(task, category_dir)
        domain = _classifyTaskDomain(task)
        expected = _DOMAIN_TO_CATEGORY.get(domain, "general")
        response = generateReasoningResponse(task, categoryDir=category_dir)
        has_conclusion = "Conclusion:" in response
        rows.append(
            {
                "session": tr.session_id,
                "provider": tr.provider,
                "model": tr.model,
                "family": modelFamily(tr.model),
                "task": task[:70],
                "mode": mode,
                "routed_category": routed,
                "expected_category": expected,
                "match": routed == expected,
                "conclusion_in_response": has_conclusion,
            }
        )

    matches = [r for r in rows if r["match"]]
    return {
        "rows": rows,
        "summary": {
            "total": len(rows),
            "routing_matches": len(matches),
            "routing_accuracy": round(len(matches) / len(rows), 3) if rows else None,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _printFidelity(report: dict) -> None:
    s = report["summary"]
    print("Extraction fidelity (extracted reasoning tokens / API-reported thinking tokens)")
    print(f"  steps with reported reasoning : {s['steps_with_reported']}")
    print(f"  mean fidelity                : {s['mean_fidelity']}")
    print(f"  opaque blocks (reported, no text): {s['opaque_count']}")
    print(f"  encrypted reasoning blocks    : {s['encrypted_block_count']}  (inventoried, not decoded)")
    print(f"  unreported reasoning steps    : {s['unreported_reasoning_steps']}")
    print(
        f"  total reported / extracted   : {s['total_reported_reasoning_tokens']} / {s['total_extracted_reasoning_tokens']}"
    )
    if report.get("family_fidelity"):
        print("  per model family:")
        for family, v in sorted(report["family_fidelity"].items()):
            print(f"    {family}: steps={v['steps']} mean_fidelity={v['mean_fidelity']}")
    for row in report["steps"]:
        fid = row["fidelity"]
        flag = "  [opaque]" if row["opaque"] else ""
        if row["unreported"]:
            flag = "  [unreported]"
        print(
            f"  {row['family']}/{row['model']} step {row['step']}: "
            f"fidelity={fid} reported={row['reported']} extracted={row['extracted']}{flag}"
        )
    if report.get("encrypted_blocks"):
        print("  encrypted block inventory:")
        for b in report["encrypted_blocks"]:
            print(
                f"    {b['family']}/{b['model']} step {b['step']}: vendor={b['vendor']} "
                f"item={b['item_id'][:12]}... chars={b['block_chars']} summary={'yes' if b['has_summary'] else 'no'}"
            )


def _printCross(report: dict) -> None:
    for task in report["tasks"]:
        print(f"\nTask: {task['task'][:90]}")
        for m in task["models"]:
            print(
                f"  {m['family']}/{m['model']}: {m['steps']} steps, "
                f"reported={m['reported_tokens']}, extracted={m['extracted_tokens']}, "
                f"fidelity={m['fidelity']}"
            )
        for p in task["pairs"]:
            j = p["reasoning_jaccard"]
            print(f"  reasoning overlap {p['a']} vs {p['b']}: jaccard={j if j is not None else 'n/a (no reasoning)'}")


def _printRouting(report: dict) -> None:
    s = report["summary"]
    print("Routing parity (TinyToT dispatch vs expected category)")
    print(f"  total / matches / accuracy : {s['total']} / {s['routing_matches']} / {s['routing_accuracy']}")
    for row in report["rows"]:
        mark = "OK " if row["match"] else "DIFF"
        print(
            f"  [{mark}] {row['family']}/{row['model']}: "
            f"mode={row['mode']} routed={row['routed_category']} expected={row['expected_category']} "
            f"| {row['task']}"
        )


def main() -> None:
    ensureUtf8Stdio()
    parser = argparse.ArgumentParser(
        description="Analyse opencode session exports for reasoning parity",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "export_dir",
        type=Path,
        nargs="?",
        default=DATA_DIR / ".sources" / "opencode",
        help="Directory of opencode session exports (JSON). Default: tinytot/_data/.sources/opencode",
    )
    parser.add_argument("--json", action="store_true", help="Emit raw JSON instead of a text report")

    sub = parser.add_subparsers(dest="cmd")
    for name in ("fidelity", "cross", "routing", "all"):
        p = sub.add_parser(name, help=f"Run the {name} parity check")
        p.add_argument(
            "--category-dir",
            type=Path,
            default=CATEGORY_DIR,
            help="Category dir for routing parity",
        )
        p.add_argument("--json", action="store_true", help="Emit raw JSON instead of a text report")

    args = parser.parse_args()
    cmd = args.cmd or "all"

    traces = parseExports(args.export_dir)
    if not traces:
        print(f"No opencode session exports found in {args.export_dir}")
        raise SystemExit(1)

    if not args.json:
        print(f"Parsed {len(traces)} opencode session export(s) from {args.export_dir}")

    results: dict = {}
    if cmd in ("fidelity", "all"):
        results["fidelity"] = fidelityReport(traces)
    if cmd in ("cross", "all"):
        results["cross_provider"] = crossProviderReport(traces)
    if cmd in ("routing", "all"):
        results["routing"] = routingReport(traces, args.category_dir)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    if "fidelity" in results:
        print("\n" + "=" * 72)
        _printFidelity(results["fidelity"])
    if "cross_provider" in results:
        print("\n" + "=" * 72)
        _printCross(results["cross_provider"])
    if "routing" in results:
        print("\n" + "=" * 72)
        _printRouting(results["routing"])


if __name__ == "__main__":
    main()
