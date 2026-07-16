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
| FFN layers | ~60% | Store facts | `data/knowledge/*.md` |
| Attention | ~25% | Route information | TF-IDF cosine sim |
| Embeddings | ~10% | Token → vector | Not needed |
| Layer norms | ~5% | Stabilise | Not needed |

TinyToT replaces the first three with zero-parameter alternatives. The only
component that genuinely needs learning is composition — estimated at **30–50M
parameters** based on LoRA, Phi-1, and distillation research.

## The four response modes

Every prompt is classified before retrieval:

```
1. JSON scoring  ← "reply with JSON", "score":, "rationale":
2. Compute       ← arithmetic, algebra, geometry, logic, letter counting
3. Direct answer ← "What is X?", "Define X", factual lookups
4. Reasoning trace ← everything else (Tree of Thoughts)
```

Priority is strict: JSON scoring beats compute, compute beats direct, direct beats
reasoning trace. Classification takes ~0.3ms, no neural network involved.

## The knowledge base

Facts are stored as paragraphs in `.md` files. Each blank-line-separated paragraph
is a **passage** — a separately searchable unit. At startup, every passage is
converted to a TF-IDF vector. Retrieval is a cosine similarity lookup.

```
Query: "What is the Heisenberg uncertainty principle?"
       ↓
TF-IDF query vector: {"heisenberg": 0.51, "uncertainty": 0.43, "principle": 0.38, ...}
       ↓
Cosine similarity against 23,881 passage vectors (~15ms)
       ↓
Top passage: "The Heisenberg uncertainty principle states that position and
              momentum cannot both be known exactly simultaneously..."
       ↓
Score 0.641 ≥ 0.50 threshold → return directly
```

## The compute engine

For arithmetic, algebra, geometry, and logic — TinyToT computes rather than
retrieves. Python's `ast` module evaluates expressions safely. `eval()` and
`exec()` are never called.

This handles problems that neural language models get wrong because they *predict*
rather than *compute*. "How many r's in strawberry?" has a correct answer (3) that
never needs to be learned from training data.

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
| Knowledge update | ✅ edit a text file | ❌ requires retraining |
| Multi-sentence synthesis | ❌ returns passages verbatim | ✅ generates fluently |
| Creative writing | ❌ no generative decoder | ✅ |
| Long document summarisation | ❌ retrieval only | ✅ full attention |
