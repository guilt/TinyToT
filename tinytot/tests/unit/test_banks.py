from pathlib import Path
from tinytot.banks import TraceBankManager

def test_split_small_stays_one(tmp_path: Path):
    src = tmp_path / "src.md"
    src.write_text("hello\n\nworld\n", encoding="utf-8")
    mgr = TraceBankManager(tmp_path / "banks", chunk_bytes=10_000)
    banks = mgr.split(src)
    assert len(banks) == 1
    assert "hello" in mgr.load(banks[0])

def test_split_large_makes_many(tmp_path: Path):
    src = tmp_path / "src.md"
    src.write_text("\n\n".join(["x" * 80] * 20), encoding="utf-8")
    mgr = TraceBankManager(tmp_path / "banks", chunk_bytes=200)
    assert len(mgr.split(src)) > 1
