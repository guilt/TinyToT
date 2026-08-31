"""tinytot.status — organism capability flags.

capability(m) = files_exist(m) AND writer_enabled(m)
"""

from __future__ import annotations

from pathlib import Path

from .sidecar import memory_dir, sense_flags, tiny_root
from . import __version__


def collect_status() -> dict:
    roots = [memory_dir(), tiny_root(), tiny_root() / "ear", tiny_root() / "eye"]
    flags = sense_flags(*roots)
    md_count = 0
    for root in roots:
        if root.exists():
            md_count += sum(1 for _ in root.rglob("*.md"))
    return {
        "tot": "ready",
        "howl": flags.get("howl", "off"),
        "ear": flags.get("ear", "off"),
        "eye": flags.get("eye", "off"),
        "counts": {"sidecar_md": md_count},
        "version": __version__,
        "memory_dir": str(memory_dir()),
        "tiny_dir": str(tiny_root()),
    }


def status_markdown(status: dict | None = None) -> str:
    s = status or collect_status()
    return (
        f"tot: {s['tot']}\n"
        f"howl: {s['howl']}\n"
        f"ear: {s['ear']}\n"
        f"eye: {s['eye']}\n"
    )


def write_status_file(path: Path | None = None) -> Path:
    path = path or (tiny_root() / "status.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(status_markdown(), encoding="utf-8")
    return path
