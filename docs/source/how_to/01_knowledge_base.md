# 01 — Knowledge Base

The knowledge base is where TinyToT's facts live. It's plain markdown.
No embeddings, no vector database, no configuration — just files.

## How it works

Every `.md` file in `tinytot/_data/knowledge/` is parsed at startup. Each blank-line-separated
paragraph becomes a **passage** — a separately searchable unit scored by TF-IDF
cosine similarity against incoming queries.

## Adding your first fact

```bash
cat >> tinytot/_data/knowledge/general.md << 'EOF'

The boiling point of ethanol is 78.37 degrees Celsius at standard pressure.
EOF

# Restart to rebuild the index
make stop run

# Query it
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"What is the boiling point of ethanol?","stream":false}'
# → "The boiling point of ethanol is 78.37 degrees Celsius at standard pressure."
```

## Creating a new knowledge file

```bash
cat > tinytot/_data/knowledge/my_domain.md << 'EOF'
# My Domain

## Key Facts

The core principle of my domain is X. This fact should lead each passage.

A second fact covers a related concept. Short paragraphs score better.

A third fact stands alone so it can be retrieved independently.
EOF
```

Rules:
- `##` headings are section labels (metadata, not passages)
- `#` top-level headings are file titles (skipped entirely)
- Each blank-line-separated paragraph is a passage
- `> source: ...` lines (Hermes format) are stripped automatically

## Writing passages that score well

**Lead with the answer:**
```markdown
# Good
Normal blood pressure is below 120/80 mmHg. Readings above this indicate hypertension.

# Bad
According to medical guidelines, the threshold for normal blood pressure is generally
considered to be below a systolic reading of 120 millimetres of mercury...
```

The good version returns "Normal blood pressure is below 120/80 mmHg" as the first
sentence — exactly what a direct query expects.

**Match the vocabulary of real queries:**
```markdown
# Good — "What is O(n²)?" will match this
O(n²) quadratic complexity means nested loops — for every element, iterate all others.

# Bad — "what is O(n²)?" won't match "doubly-nested iteration"
Quadratic time complexity is exhibited by algorithms with doubly-nested iteration.
```

**One fact per paragraph:**
```markdown
# Good — each can be retrieved independently
The atomic number of carbon is 6.

The atomic number of oxygen is 8.

# Bad — only one passage, harder to rank precisely
Carbon has atomic number 6 and oxygen has atomic number 8, while nitrogen has 7.
```

## Confidence thresholds

Retrieval uses **five-head scoring** (TF-IDF unigrams, conclusion TF-IDF, character
trigrams, BM25, keyword frontmatter). The final score is a weighted blend. Two-stage:
O(N) TF-IDF coarse scan → multi-head re-rank of top-20 candidates.

| Score | What happens |
|---|---|
| `≥ 0.65` | Passage returned directly, no ToT wrapper |
| `0.25–0.65` | Passage used for direct/yes-no answers and grounding |
| `< 0.20` | No knowledge match — pure reasoning chain |

## Diagnosing retrieval misses

```bash
pipenv run python3 << 'EOF'
from tinytot.retrieval import buildKnowledgeIndex, queryVector, cosineSim
from tinytot.content import loadKnowledgePassages
buildKnowledgeIndex.cache_clear(); loadKnowledgePassages.cache_clear()
entries, idf, vecs = buildKnowledgeIndex()

query = "your failing query here"
qvec = queryVector(query, idf)
scored = sorted(
    [(cosineSim(qvec, dv), t[:70]) for (_, t), dv in zip(entries, vecs)],
    reverse=True
)
print(f"Top 5 for: '{query}'")
for score, text in scored[:5]:
    print(f"  {score:.3f}  {text}")
EOF
```

If the right passage isn't in the top 5, rewrite it to lead with the answer and
use the exact vocabulary from the query.

## Next Steps

- **[Compute Engine](02_compute_engine.md)** — for calculations, not retrieval
- **[Hermes Bridge](05_hermes_bridge.md)** — auto-ingest agent learnings
- **[Ingesting Corpora](08_ingesting_corpora.md)** — bulk-load external datasets
