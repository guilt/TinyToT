# Core Concepts

Understanding TinyToT's architecture makes everything else click.

## The central insight

Every large language model does two completely different things:

1. **Fact storage** — memorising billions of facts in weight matrices
2. **Composition** — combining retrieved facts into coherent answers

Standard LLMs use the same mechanism — gradient descent — for both.
This is expensive, lossy, and makes facts impossible to update without retraining.

TinyToT separates them. Facts live in plain text files. Routing is TF-IDF cosine
similarity. Only the final composition step needs learned parameters — and that
needs far fewer than people assume.

## The parameter arithmetic

Research (Geva et al. 2021, Meng et al. 2022) shows that FFN layers in transformers
act as key-value memories — individual neurons fire for specific facts. A 7B model
spends roughly:

| Component | % of params | What it does | TinyToT equivalent |
|---|---|---|---|
| FFN layers | ~60% | Store facts | `tinytot/_data/knowledge/*.md` |
| Attention | ~25% | Route information | TF-IDF cosine sim |
| Embeddings | ~10% | Token → vector | Not needed |
| Layer norms | ~5% | Stabilise | Not needed |

TinyToT replaces the first three with zero-parameter alternatives. The only
component that genuinely needs learning is composition — estimated at **30–50M
parameters** based on LoRA, Phi-1, and distillation research.

## The ten dispatch stages

Every prompt is classified and dispatched through ten stages, first-match-wins:

```
0a. Normalise          ← clean / lowercase, expand contractions
0b. Multi-turn refine  ← code refinement intents (10 intents), AST code explanation
0c. Project scaffold   ← "create a flask app", "scaffold a CLI" (5 blueprints)
0d. Use-case handler   ← 10 handlers: rewrite_code, rewrite, extract, table,
                          brainstorm, debug_inline, howto, uncertainty,
                          multidoc, creative
1.  JSON scoring       ← "reply with JSON", "score":, "rationale":
2.  Summarize          ← "summarize", "tl;dr", long text
3.  Compute            ← arithmetic, algebra, geometry, logic, letter counting,
                          propositional chains, coreference, contradiction,
                          structured data, fraction-of-total, chained %
4.  Social             ← greetings, small-talk
5.  Agent              ← tool-calling dispatch
6.  Live data          ← "current weather", "stock price"
7.  Knowledge base     ← factual question (five-head retrieval, threshold 0.65)
8.  Code generation    ← "write/implement a function" (648 templates, 7+ languages)
9.  Tree of Thoughts   ← default reasoning (multi-path chain search)
```

Priority is strict: each stage beats all stages below it. Classification takes
~0.3ms; no neural network is involved at any stage.

## The knowledge base

Facts are stored as paragraphs in `.md` files. Each blank-line-separated paragraph
is a **passage** — a separately searchable unit. At startup, every passage is
indexed for retrieval.

Retrieval uses a **two-stage five-head** pipeline:

1. **Coarse scan** — fast TF-IDF pass over all passages to select the top-20
   candidates.
2. **Multi-head re-rank** — five independent scorers vote on the top-20:

| Head | Method |
|---|---|
| H1 | TF-IDF unigrams |
| H2 | Conclusion TF-IDF (last-sentence emphasis) |
| H3 | Character trigram similarity |
| H4 | BM25 |
| H5 | Keyword frontmatter matching |

The highest-scoring passage is returned if its score meets the
`KNOWLEDGE_DIRECT_THRESHOLD` of **0.65**. Q&A-format passages receive a 1.15×
relevance bonus (capped at 1.0 in the multi-head context). Noisy corpora
(benchmark Q&A, fill-in-the-blank) receive a **0.6× penalty**.

```
Query: "What is the Heisenberg uncertainty principle?"
       ↓
Coarse TF-IDF scan → top-20 candidates (~8ms)
       ↓
Five-head re-rank → weighted vote
       ↓
Top passage score 0.71 ≥ 0.65 threshold → return directly
```

## The compute engine

For arithmetic, algebra, geometry, and logic — TinyToT computes rather than
retrieves. Python's `ast` module evaluates expressions safely. `eval()` and
`exec()` are never called.

The engine handles: arithmetic, algebra, geometry, percentages, unit conversion,
date math, letter counting, propositional logic chains (A→B→C), coreference
resolution, contradiction detection, structured data comparisons, fraction-of-total
problems, chained percentage calculations, and multi-step word problems.

## Multi-turn code refinement

`refine.py` handles iterative code improvement across **10 intents**: make_async,
add_types, add_error_handling, add_logging, add_docstring, simplify, optimize,
translate, add_tests, explain. It uses AST parsing for structural awareness —
not string substitution. The `explain` intent runs AST-based code explanation.

## Use-case handlers

`generate.py` implements 10 named handlers that match structured use-case
patterns before the main dispatch chain. All patterns are declared in
`tinytot/_data/generate/use_cases.yaml`:

| Handler | What it produces |
|---|---|
| `rewrite_code` | Idiomatic/Pythonic rewrite of supplied code |
| `rewrite` | Prose rewrite (style, tone, length, formality) |
| `extract` | Structured entity extraction (emails, URLs, dates…) |
| `table` | Markdown comparison table or pros/cons |
| `brainstorm` | Numbered idea list |
| `debug_inline` | Static analysis of pasted code (19 checks) |
| `howto` | Step-by-step instructions (15+ guides in YAML) |
| `uncertainty` | Calibrated "I don't know" with reasoning |
| `multidoc` | Cross-document synthesis and contradiction detection |
| `creative` | Haiku, poem, story continuation, dialogue |

## Project scaffolding

`generateProject()` in `codegen.py` generates complete multi-file project
structures from five blueprints in `tinytot/_data/codegen/projects.yaml`:
`flask_api`, `fastapi_api`, `python_cli`, `data_pipeline`, `python_package`.
Add new blueprints by editing the YAML file — no code changes needed.

## The Hermes bridge

TinyToT auto-detects Hermes Learning Journal files. Any `.md` file with the
`> source: ... · hash: ...` provenance format is parsed as a Hermes journal —
each `##` heading is a learning entry. This means:

**Hermes learns during a session → writes a journal file → TinyToT retrieves
those learnings at the next query — without retraining.**

## When TinyToT wins vs. transformers

| Task | TinyToT | Transformer |
|---|---|---|
| Factual recall | ✅ 100% accurate, 0 hallucination | ✅ but ~5-15% error rate |
| Arithmetic | ✅ exact computation | ❌ token prediction, often wrong |
| Letter counting | ✅ always correct | ❌ common failure mode |
| Propositional logic chains | ✅ deterministic A→B→C | ❌ unreliable |
| Knowledge update | ✅ edit a text file | ❌ requires retraining |
| Multi-turn code refinement | ✅ AST-aware, 10 intents | ✅ but can drift |
| Use-case structured output | ✅ template-driven, 10 handlers | ✅ but inconsistent |
| Project scaffolding | ✅ 5 blueprints, always complete | ✅ but can hallucinate |
| Multi-sentence synthesis | ❌ returns passages verbatim | ✅ generates fluently |
| Creative writing | ❌ template-bound | ✅ |
| Long document summarisation | ❌ retrieval only | ✅ full attention |
