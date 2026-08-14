# 08 — Ingesting Corpora

TinyToT has two kinds of data you can feed it: **knowledge passages**
(facts → `tinytot/_data/knowledge/`) and **code templates** (programs → `tinytot/_data/codegen/`).
Both use plain text files. No training, no fine-tuning, no GPU.

---

## 1 — How the model uses ingested data

```
query
  │
  ├─ knowledge lookup  →  tinytot/_data/knowledge/*.md   (TF-IDF cosine similarity)
  ├─ code generation   →  tinytot/_data/codegen/templates/*.md  (pattern → template)
  └─ routing           →  tinytot/_data/categories/*.md  (TF-IDF cosine similarity)
```

Ingested data flows into the model's response at query time — no restart
is needed for code templates. The knowledge and routing indexes are cached
per-process; after adding new knowledge files, hot-reload with
`curl -X POST http://localhost:11434/api/reload` or restart the server.

> Note: auto-ingested trace chains (`opencode_augment_*`, `opentraces_augment_*`)
> are excluded from the routing index by design — see the
> [opencode ingestion](#ingest-opencode-session-traces) section below.

---

## 2 — Ingesting knowledge passages

Knowledge passages live in `tinytot/_data/knowledge/`. Every `.md` file is indexed.
Each non-empty paragraph (separated by a blank line) becomes one passage.

### Format

```markdown
# My Domain

## My Topic

Plain prose works: TinyToT scores this passage against queries using TF-IDF.

Q: What is compound interest? A: Compound interest is interest calculated on
both the principal and accumulated interest.

Q: What is the Pythagorean theorem? A: a² + b² = c² for a right triangle.
```

- **Q: ... A: ...** format gets a 1.15× relevance boost (the answer token
  is in the passage, improving cosine similarity to "what is X?" queries).
- Plain prose works for longer explanations.
- Lead with the answer: "Paris is the capital of France" scores higher for
  "What is the capital of France?" than "France's capital is Paris."

### Add a knowledge file

```bash
# Create the file
cat > tinytot/_data/knowledge/my_domain.md << 'EOF'
# My Domain

## My Domain

Q: What is X? A: X is Y.
Q: How does Z work? A: Z works by...
EOF

# Restart to rebuild the index
make stop run

# Verify it loaded
pipenv run python3 -c "
from tinytot.retrieval import buildKnowledgeIndex
from tinytot.content import loadKnowledgePassages
buildKnowledgeIndex.cache_clear(); loadKnowledgePassages.cache_clear()
_, _, vecs = buildKnowledgeIndex()
print(f'{len(vecs)} passages in index')
"
```

### Ingest GSM8K (grade school math)

```bash
# The GSM8K test JSONL is NOT shipped in the wheel (it is a large external
# dataset). Provide the path to a GSM8K JSONL explicitly:
tinytot-ingest gsm8k /path/to/gsm8k_test.jsonl
```

Each GSM8K record becomes a Q/A passage:
```
Q: Natalia sold clips to 48 friends in April and half as many in May.
Step 1: She sold 48/2 = 24 clips in May.
Step 2: She sold 48 + 24 = 72 clips altogether.
Answer: 72
```

### Ingest Princeton ToT traces

```bash
# Clones (or updates) the princeton-nlp/tree-of-thought-llm repo and ingests
# the game24 + creative-writing traces:
tinytot-ingest tot-princeton
```

Produces:
- `tinytot/_data/categories/game24.md` — reasoning chains for the 24-game
- `tinytot/_data/categories/creative_writing.md` — text coherence chains

### Ingest opencode session traces

`opencode export` produces one JSON file per session. TinyToT ingests them as
reasoning chains, preserving parity metadata (provider, model, token counts) in
chain comments:

```bash
# Export sessions (opencode CLI must be on PATH)
opencode export <session-id> -o tinytot/_data/.sources/opencode/

# Ingest the exports
tinytot-ingest opencode

# Optional: auto-export a session id before ingesting (repeatable)
tinytot-ingest opencode --session <session-id>
```

Produces `tinytot/_data/categories/opencode_augment_*.md` — one file per
classified domain (e.g. `opencode_augment_debug.md`, `opencode_augment_general.md`,
`opencode_augment_programming.md`). Each session's task is classified by domain
via `_classifyTaskDomain` (including the `math` domain for rate word problems)
and appended as a `## Chain N:` entry.

- Augment files are **excluded from the routing index** (`buildChainIndex` skips
  `opencode_*` / `opentraces_augment_*` files) so they don't pollute routing.
- They are loaded for reasoning and parity analysis via `loadOpenCodeChains`.
- Use `--limit N` to cap sessions and `--max-chains N` to cap chains per category.
- See [Reasoning Chains](03_reasoning_chains.md) for the chain format.

### Ingest OpenTraces (Hugging Face)

```bash
tinytot-ingest opentraces
```

Downloads OpenTraces agent reasoning traces from Hugging Face and classifies
each trace by domain, appending chains to the matching existing category
(e.g. `python` → programming, `debugging` → debug). Traces that don't map to an
existing category are written to `opentraces_augment_general_*`.

### Ingest everything

```bash
tinytot-ingest all
```

### Ingest BIG-bench tasks

```python
import json
from pathlib import Path

base = Path('/path/to/bigbench/bigbench/benchmark_tasks')
out = Path('data/knowledge')

def ingest_task(name, label, limit=500):
    d = json.loads((base / name / 'task.json').read_text())
    lines = [f'# {label}\n\n## {label}\n']
    for ex in d['examples'][:limit]:
        inp = str(ex.get('input', '')).strip()[:300]
        scores = ex.get('target_scores', {})
        answer = max(scores, key=scores.get) if scores else str(ex.get('target', ''))
        if inp and answer:
            lines.append(f'Q: {inp} A: {answer}.\n')
    (out / f'{name.replace("_", "-")}.md').write_text('\n'.join(lines))

ingest_task('causal_judgment', 'Causal Reasoning', 190)
ingest_task('temporal_sequences', 'Temporal Sequence Reasoning', 500)
```

### Write your own ingestor

```python
# tinytot/ingest.py — add a new subcommand
def ingest_my_format(source: Path, out_file: Path, limit: int = 0) -> int:
    records = json.loads(source.read_text())
    if limit:
        records = records[:limit]
    lines = ['# My Domain\n\n## My Domain\n']
    for rec in records:
        q = rec['question'].strip()
        a = rec['answer'].strip()
        lines.append(f'Q: {q} A: {a}\n')
    out_file.write_text('\n'.join(lines), encoding='utf-8')
    return len(records)
```

Then register it in `main()` in `tinytot/ingest.py` as a subcommand.

---

## 3 — Ingesting code generation templates

Code templates live in `tinytot/_data/codegen/templates/`. Each `.md` file covers
one algorithm or problem. Changes take effect immediately — no restart needed.

### Template format

```markdown
# Reverse String

## python
```python
def reverse_string(s: str) -> str:
    """Return the reverse of string s."""
    return s[::-1]
```

## javascript
```javascript
function reverseString(s) {
    return s.split('').reverse().join('');
}
```

## go
```go
func reverseString(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}
```
```

Rules:
- One `## <language>` section per language.
- Language names must be lowercase and match entries in `tinytot/_data/codegen/config.yaml`.
- Fenced block label: use `cpp` for C++, `csharp` for C#; all others match the language name.
- **Never include a demo `fn main()` / `int main()` inside the function section** —
  the execution test harness appends its own `main`. Functions only.
- The first template entry (usually Python) is used as the fallback for languages
  that don't have their own section yet.

### Register a pattern

Add an entry to `tinytot/_data/codegen/patterns.yaml`:

```yaml
  - pattern: '\breverse\s+string\b|\breverse\s+a\s+string\b'
    key: reverse_string
    note: "Reverse String"
```

The `key` must match the filename (without `.md`). Patterns are tested in order —
put more specific patterns before broad ones.

### Ingest from the guilt/Code mirror

If you have a local mirror of guilt.github.io/Code (e.g. via HTTrack):

```bash
# The mirror is already ingested at tinytot/_data/codegen/templates/ (140+ problems)
# To re-ingest from a new mirror location:
python3 - << 'EOF'
from pathlib import Path
import re

MIRROR = Path('/path/to/mirror/Problems')

for f in sorted(MIRROR.glob('*.html')):
    html = f.read_text(errors='replace')
    code_m = re.search(r'<div class="language-python[^>]*>(.*?)</div>', html, re.DOTALL)
    if not code_m: continue
    code = re.sub(r'<[^>]+>', '', code_m.group(1))
    code = code.replace('&gt;','>').replace('&lt;','<').replace('&amp;','&').strip()
    if len(code) < 20: continue

    stem = f.stem.lstrip('0123456789-').lstrip('XXX-')
    # CamelCase to snake_case
    key = re.sub(r'([A-Z])', r'_\1', stem).lower().lstrip('_')
    out = Path(f'tinytot/_data/codegen/templates/{key}.md')
    out.write_text(f'# {stem}\n\n## python\n```python\n{code}\n```\n')
    print(f'  {key}.md')
EOF
```

Then add patterns for the new templates in `tinytot/_data/codegen/patterns.yaml`.

### Check coverage

```bash
pipenv run python3 -m tinytot.benchmark codegen
```

Shows which of the 49 benchmark cases pass and which languages have real
implementations vs. Python-fallback stubs.

---

## 4 — After ingesting knowledge

```bash
# Rebuild the index
make stop run

# Verify passage count
pipenv run python3 -c "
from tinytot.retrieval import buildKnowledgeIndex
from tinytot.content import loadKnowledgePassages
buildKnowledgeIndex.cache_clear(); loadKnowledgePassages.cache_clear()
_, _, vecs = buildKnowledgeIndex()
print(f'{len(vecs)} passages in index')
"

# Run benchmarks to measure accuracy
make bench
```

---

## 5 — Troubleshooting

**Query returns wrong passage:** The knowledge base may have noisy passages
(from large corpora like epistemic-reasoning datasets) that score higher than
your targeted passage. Fix: add the Q/A format for your fact — the 1.15× boost
will push it above the noise.

**Code generation ignores a new template:** Check that the pattern in
`patterns.yaml` matches your test query. More specific patterns must come
before broader ones. Run:

```bash
pipenv run python3 -c "
from tinytot.codegen import _matchPattern, _loadPatterns
_loadPatterns.cache_clear()
print(_matchPattern('your test query here'))
"
```

**Server returns stale results after adding knowledge:** The index is cached
in-process. Run `make stop run` to rebuild.

---

## Next Steps

- **[Knowledge Base](01_knowledge_base.md)** — writing targeted Q/A passages
- **[Code Generation](10_code_generation.md)** — adding templates and patterns
- **[Benchmarking](07_benchmarking.md)** — measuring accuracy after ingestion
