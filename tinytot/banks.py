"""Split huge markdown banks; one active bank in RAM."""
from __future__ import annotations
from pathlib import Path

class TraceBankManager:
    def __init__(self, root: Path, chunk_bytes: int = 512_000) -> None:
        self.root = root
        self.chunk_bytes = chunk_bytes
        self.active: Path | None = None

    def split(self, source: Path, prefix: str = "bank") -> list[Path]:
        self.root.mkdir(parents=True, exist_ok=True)
        text = source.read_text(encoding="utf-8")
        if len(text.encode("utf-8")) <= self.chunk_bytes:
            dest = self.root / f"{prefix}-000.md"
            dest.write_text(text, encoding="utf-8")
            return [dest]
        parts = text.split("\n\n")
        banks, buf, size, idx = [], [], 0, 0
        for part in parts:
            piece = part + "\n\n"
            n = len(piece.encode("utf-8"))
            if buf and size + n > self.chunk_bytes:
                dest = self.root / f"{prefix}-{idx:03d}.md"
                dest.write_text("".join(buf), encoding="utf-8")
                banks.append(dest)
                idx += 1
                buf, size = [], 0
            buf.append(piece)
            size += n
        if buf:
            dest = self.root / f"{prefix}-{idx:03d}.md"
            dest.write_text("".join(buf), encoding="utf-8")
            banks.append(dest)
        return banks

    def load(self, path: Path) -> str:
        self.active = path
        return path.read_text(encoding="utf-8")
