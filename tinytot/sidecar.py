"""tinytot.sidecar — ingest *.eye.md / *.ear.md pairs.

Indexes yaml header + ## Belief only. Does not index .pt, raw audio, or jpeg bytes.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

SIDECAR_SUFFIXES = (".eye.md", ".ear.md")
BELIEF_HEADING = re.compile(r"^##\s+Belief\s*$", re.MULTILINE | re.IGNORECASE)
NEXT_HEADING = re.compile(r"^##\s+", re.MULTILINE)


def memory_dir() -> Path:
    if env := os.environ.get("TINYTOT_MEMORY_DIR"):
        return Path(env)
    if data := os.environ.get("TINYTOT_DATA_DIR"):
        return Path(data).parent / "memory"
    return Path.cwd() / "memory"


def tiny_root() -> Path:
    if env := os.environ.get("TINYTOT_TINY_DIR"):
        return Path(env)
    return Path.cwd() / "tiny"


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, Any] = {}
    if yaml is not None:
        loaded = yaml.safe_load(raw) or {}
        if isinstance(loaded, dict):
            meta = loaded
    else:
        for line in raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, body


def extract_belief(body: str) -> str:
    m = BELIEF_HEADING.search(body)
    if not m:
        return ""
    rest = body[m.end() :]
    n = NEXT_HEADING.search(rest)
    chunk = rest[: n.start()] if n else rest
    return chunk.strip()


@dataclass
class Sidecar:
    path: Path
    modality: str
    meta: dict[str, Any] = field(default_factory=dict)
    belief: str = ""
    evidence_path: str | None = None

    @property
    def belief_ok(self) -> bool:
        if self.meta.get("belief_ok") is False:
            return False
        if self.meta.get("transcript_ok") is False and self.modality == "ear":
            return bool(self.belief)
        return bool(self.belief.strip())

    def passage_text(self) -> str:
        bits = [self.belief.strip()] if self.belief.strip() else []
        if not bits:
            return ""
        src = self.meta.get("source", "")
        when = self.meta.get("time", "")
        header = " ".join(x for x in (when, src, self.modality) if x)
        return f"{header}\n{bits[0]}".strip() if header else bits[0]


def parse_sidecar(path: Path) -> Sidecar | None:
    name = path.name
    modality = ""
    if name.endswith(".eye.md"):
        modality = "eye"
    elif name.endswith(".ear.md"):
        modality = "ear"
    else:
        return None
    text = path.read_text(encoding="utf-8")
    meta, body = _split_frontmatter(text)
    meta.setdefault("modality", modality)
    belief = extract_belief(body)
    stem = path.name[: -len(f".{modality}.md")]
    evidence = None
    for ext in (".jpg", ".jpeg", ".png", ".opus", ".wav", ".adpcm"):
        cand = path.with_name(f"{stem}.{modality}{ext}")
        if cand.exists():
            evidence = str(cand)
            break
    return Sidecar(path=path, modality=modality, meta=meta, belief=belief, evidence_path=evidence)


def iter_sidecars(*roots: Path) -> list[Sidecar]:
    found: list[Sidecar] = []
    seen: set[Path] = set()
    for root in roots:
        if not root or not root.exists():
            continue
        for p in sorted(root.rglob("*.md")):
            rp = p.resolve()
            if rp in seen:
                continue
            if not any(p.name.endswith(s) for s in SIDECAR_SUFFIXES):
                continue
            seen.add(rp)
            sc = parse_sidecar(p)
            if sc:
                found.append(sc)
    return found


def write_sidecar(
    out_dir: Path,
    stem: str,
    modality: str,
    belief: str,
    meta: dict[str, Any] | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.{modality}.md"
    fields = {
        "modality": modality,
        "time": "",
        "source": "hand",
        "confidence": 0.4,
        "belief_ok": bool(belief.strip()),
    }
    if meta:
        fields.update(meta)
    lines = ["---"]
    for k, v in fields.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append("## Belief")
    lines.append(belief.strip() or "")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def sidecar_passages(*roots: Path) -> list[tuple[str, str]]:
    """(heading, passage) pairs TinyToT can treat as knowledge after reload."""
    out: list[tuple[str, str]] = []
    for sc in iter_sidecars(*roots):
        text = sc.passage_text()
        if not text:
            continue
        heading = f"sidecar:{sc.modality}:{sc.path.name}"
        out.append((heading, text))
    return out


def sense_flags(*roots: Path) -> dict[str, str]:
    flags = {"ear": "off", "eye": "off"}
    for sc in iter_sidecars(*roots):
        flags[sc.modality] = "ready"
    howl = os.environ.get("TINYTOT_HOWL", "off")
    flags["howl"] = howl if howl in ("off", "ready") else "off"
    return flags
