# 05 — Hermes Bridge

TinyToT automatically reads Hermes Learning Journal files. This is the bridge
between organic agent learning and zero-parameter inference: **Hermes learns →
writes markdown → TinyToT answers from it without retraining.**

## How Hermes journals work

When you use `/learn` in Hermes (or Hermes records a learning automatically),
it writes a daily file like `2026-07-01.md`:

```markdown
# 2026-07-01

## Always prefer async/await for I/O-bound operations in Python services.
> source: user · 2026-07-01T10:00:00+00:00 · hash: abc123...

## The PFC ledger service uses optimistic locking with version vectors.
> source: agent · 2026-07-01T11:00:00+00:00 · hash: def456...
```

Each `##` heading is a learning. The `> source:` line is provenance metadata.

## Adding Hermes learnings to TinyToT

```bash
# Copy a Hermes daily journal into TinyToT's knowledge base
cp ~/.config/hermes/learnings/2026-07-01.md tinytot/_data/knowledge/

# Restart to index it
make stop run

# Query a learning
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"How should I handle I/O in Python services?","stream":false}'
# → "Always prefer async/await for I/O-bound operations in Python services."
```

## How TinyToT detects the format

TinyToT scans each `.md` file for the Hermes provenance pattern:
```
> source: <word> · <timestamp> · hash: <64-hex-chars>
```

If found anywhere in the file, the entire file is parsed as a Hermes journal.
Plain knowledge files (no provenance lines) are parsed normally. The two formats
coexist without any configuration.

## Automatic sync (suggested workflow)

```bash
# Sync all today's learnings into TinyToT
cp ~/.config/hermes/learnings/$(date +%Y-%m-%d).md tinytot/_data/knowledge/
make stop run
```

Or set up a cron/watch that copies new journal files automatically.

## What the learning flow looks like end to end

```
Hermes session                    TinyToT
─────────────────                 ─────────────────────────────
/learn "prefer async/await"  →    tinytot/_data/knowledge/2026-07-01.md
                                  (copied in)
                              →   restart server
                              →   TF-IDF index includes:
                                  "Always prefer async/await
                                   for I/O-bound operations..."
New prompt:
"How to handle I/O in Python?" →  cosine sim → score 0.23
                              →   knowledge grounding in trace
                              →   "Always prefer async/await..."
```

No gradient descent. No retraining. No embedding pipeline.
The learning is in the text. Retrieval finds it.

## Next Steps

- **[Knowledge Base](01_knowledge_base.md)** — write knowledge directly
- **[Extending TinyToT](09_extending.md)** — add new journal formats
