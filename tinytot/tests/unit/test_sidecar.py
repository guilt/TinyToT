from pathlib import Path

from tinytot.sidecar import parse_sidecar, sidecar_passages, write_sidecar
from tinytot.truth import MISS


def test_write_and_parse(tmp_path: Path):
    p = write_sidecar(
        tmp_path,
        stem="2026-08-30T15-00-00",
        modality="eye",
        belief="A mug on a desk.",
        meta={"source": "hand", "time": "2026-08-30T15:00:00Z", "confidence": 0.4},
    )
    assert p.name.endswith(".eye.md")
    sc = parse_sidecar(p)
    assert sc is not None
    assert sc.modality == "eye"
    assert "mug" in sc.belief.lower()
    passages = sidecar_passages(tmp_path)
    assert passages
    assert "mug" in passages[0][1].lower()


def test_empty_belief_is_not_a_passage(tmp_path: Path):
    write_sidecar(tmp_path, stem="blank", modality="eye", belief="")
    assert sidecar_passages(tmp_path) == []


def test_miss_string_is_grepable():
    assert "I don't know" in MISS
