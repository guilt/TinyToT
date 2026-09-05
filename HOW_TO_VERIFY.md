# HOW_TO_VERIFY — Tiny organism contracts (bananey)

Tiny is a markdown cache that can grow ears, a mouth, and borrowed eyes.
If a sense is missing it says so. Port 11434. Files you can delete.

Self-benches measure **consistency with the cache**, not discovery of the world.

## Family extras (git until PyPI)

TinyToT does not require a mouth, ears, or borrowed eyes. Opt in:

```bash
pip install -e ".[howl]"     # tinyhowl @ git+https://github.com/guilt/tinyhowl.git@bananey
pip install -e ".[ear]"
pip install -e ".[eye]"
pip install -e ".[nano]"
pip install -e ".[family]"   # all four
```

After each package is on PyPI the extras become version pins (`tinyhowl>=0.1.2`, …).

Miss string (grep this everywhere):

```
I don't know. That is not in my knowledge base.
```

## Unit (no server)

```bash
python -m pytest tinytot/tests/unit/test_truth.py tinytot/tests/unit/test_sidecar.py -q
```

## Server curls (after `tinytot` on 11434)

Unknown fact — must not invent a capital or a date. Wire `TINYTOT_HONEST_MISS=1`
once inference is hooked; until then the unit tests own the miss contract.

```bash
curl -s http://127.0.0.1:11434/api/status
# eye: off if no eye files

curl -s -X POST http://127.0.0.1:11434/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"modality":"eye","stem":"demo-mug","belief":"A mug on a desk."}'

curl -s -X POST http://127.0.0.1:11434/api/reload

curl -s http://127.0.0.1:11434/api/status
# eye: ready after the sidecar exists
```

Drop a hand-written pair and reload:

```bash
mkdir -p memory
cat > memory/2026-08-30T15-00-00.eye.md << 'EOF'
---
modality: eye
time: 2026-08-30T15:00:00Z
source: hand
confidence: 0.4
belief_ok: true
---

## Belief
A mug on a desk.
EOF

curl -s -X POST http://127.0.0.1:11434/api/reload
```

Ask about that belief after hook-up. No eye files + "see?" → miss, not a caption.
