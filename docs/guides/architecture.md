# TinyToT Architecture and Vision

## What TinyToT is

TinyToT is an **inference engine without learnable parameters**. It answers
questions, generates code, summarizes documents, and scores responses — all
from data files and algorithmic dispatch. No gradient descent, no GPU, no
billion-dollar training run.

This document explains how it works, how it differs from large language models,
and where it can go next.

---

## How the pieces fit together

### The dispatch pipeline

Every prompt enters a single function (`generateReasoningResponse`) and passes
through seven stages, first-match-wins:

```
prompt
  │
  ├─ 1. JSON scoring      "reply with json" / eval rubric
  │     → {"score": 0.8, "rationale": "..."}
  │
  ├─ 2. Summarization     "summarize" / "tl;dr" / long text
  │     → extractive summary from arc-aware sentence election
  │
  ├─ 3. Compute           arithmetic / unit conversion / date math
  │     → exact numeric result (no token prediction)
  │
  ├─ 4. Live data         "current weather" / "stock price"
  │     → honest refusal ("I don't have real-time data")
  │
  ├─ 5. Knowledge base    factual question
  │     → TF-IDF cosine similarity over 23,000+ passages
  │
  ├─ 6. Code generation   "write/implement a function"
  │     → template from data/codegen/templates/
  │
  └─ 7. Tree of Thoughts  default reasoning
        → multi-path chain search with knowledge grounding
```

Each stage reads from **data files**, not from neural weights.

### The five systems

**Knowledge retrieval** (`tinytot/retrieval.py`)
TF-IDF cosine similarity over `data/knowledge/*.md`. Each paragraph is one
passage. Q/A format passages get a 1.15× relevance boost. Large noisy corpora
(epistemic reasoning, dialogue inference) get a 0.6× penalty. Current size:
23,886 passages, built from GSM8K, BIG-bench, HumanEval, and domain writing.

**Compute engine** (`tinytot/compute.py`)
Deterministic solvers for: arithmetic, algebra (linear equations), geometry
(8 formulas), percentages, unit conversion, date arithmetic, word problems,
and logical deduction (modus ponens/tollens). Never uses token prediction.
Results are always exact.

**Code generation** (`tinytot/codegen.py`)
Pattern matching (`data/codegen/patterns.yaml`) → template lookup
(`data/codegen/templates/<key>.md`). 189 templates, 7 languages, 300+ patterns.
Language detection and request detection patterns live in `data/codegen/config.yaml`.
Compositional problems (median = sort + index) are decomposed in
`data/codegen/decompositions.yaml` and annotated in the output.

**Summarization** (`tinytot/summarize.py`)
Arc-aware sentence election: the document is split into narrative arcs
(setup/complication/crisis/resolution), and the best sentence per arc is
elected using: entity density × plot-verb weight × outcome-signal boost ×
IDF score × position boost. For short passages (< ARC_THRESHOLD sentences)
the arc-aware path is used. For very short passages the flat TF-IDF
centrality path runs. Output quality: 11/11 on 11-domain eval spanning
climate science, medical trials, contract law, WWII history, fiction, and more.

**Tree of Thoughts** (`tinytot/inference.py`)
Multi-path reasoning over `data/categories/*.md` chains. Each category has
15 chains (capped to prevent large corpora dominating IDF). The best chain
is selected by TF-IDF cosine similarity to the prompt. If a knowledge passage
scores above `KNOWLEDGE_THRESHOLD`, it grounds the chain.

---

## How it differs from an LLM

### The same

- Accepts natural language prompts
- Returns natural language responses
- Handles factual Q&A, code, math, summarization
- Accessible via Ollama-compatible API (same port 11434)
- Routing by content: the system detects what kind of question is being asked

### Fundamentally different

| Dimension | TinyToT | Large Language Model |
|---|---|---|
| **Parameters** | 0 learnable | 1B–70B+ weights |
| **Training** | None | Weeks on GPU clusters |
| **Knowledge update** | Edit a text file, restart | Retrain or fine-tune |
| **Arithmetic** | Deterministic (always correct) | Probabilistic (often wrong) |
| **Hallucination** | Impossible for KB facts | Inherent to generation |
| **Explainability** | Every answer has a source passage | Attention weights don't explain |
| **Cost** | CPU, <1GB RAM, 126 QPS | GPU, 16–80GB VRAM |
| **Latency** | <10ms for KB lookups | 200ms–10s depending on size |
| **Synthesis** | ❌ returns passages, not new text | ✅ generates novel sentences |
| **Code generation** | ✅ template-driven, always runnable | ✅ but can hallucinate APIs |
| **Long context** | Limited (extractive summarization) | ✅ full attention window |

The architectural difference is this: an LLM **memorises** facts in parameters
and **synthesises** answers. TinyToT **indexes** facts in text and **retrieves**
answers. This trades synthesis for correctness, speed, and updatability.

---

## Why it requires almost no training

The hard parts of LLM training are:
1. **Fact injection**: forcing facts into weight matrices
2. **Instruction following**: making the model respond as asked
3. **Format compliance**: making output consistently structured

TinyToT solves all three without training:
1. Facts go into `data/knowledge/*.md` (text files, not weights)
2. Instruction following is deterministic dispatch (code, not learned)
3. Format compliance is template instantiation (also code)

What *would* require training: **synthesis** — generating fluent novel
sentences that combine facts in new ways. TinyToT can't write a paragraph
that wasn't in the training data. That requires a ~30–50M parameter
composition head. Everything else it does better without one.

---

## Cost and development benefits

**Zero training cost**: No GPU, no data pipeline, no experiment tracking.
Adding a new domain takes minutes, not weeks.

**Zero serving cost**: Runs on a CPU at 126 QPS. A $50/month server handles
production load.

**Zero hallucination on facts**: If a fact isn't in `data/knowledge/`, the
model says so. If it is, it returns the exact passage.

**Instant knowledge update**: Edit a `.md` file, restart the server (10 seconds).
Compare to fine-tuning a 7B model (hours to days, thousands of dollars).

**Full auditability**: Every answer cites an implicit source (which knowledge
file, which passage). Debugging is `grep`.

**Test-driven development**: The full benchmark suite runs in 30 seconds.
`make bench` shows routing, retrieval, summarization, code generation, and GSM8K
accuracy as ASCII bar charts. Pre-commit hooks prevent regressions.

---

## Where we can do radically amazing things

### 1. Multi-language code generation (currently: 7 languages)

Every language is just a `## <language>` section in a `.md` file. Adding
Swift to all 189 templates is a weekend project. Adding Kotlin, Scala, Elixir,
Zig, or any other language is zero Python, zero retraining.

**Vision**: Generate runnable code in 40+ languages from a single query.
Pattern: write the algorithm once in Python, auto-translate using any existing
translator (or manually). Each language section is independently testable.

### 2. Multi-modal input (documents, images, audio transcripts)

Currently TinyToT only processes text. But the retrieval pipeline doesn't care
about the source format — it needs tokenized text.

**PDF/document processing**: A tool like
[pdf-translate](https://github.com/guilt/pdf-translate) can extract text from
PDFs and translated documents. Feed that text to `summarizeDocument()` or
`findKnowledgeAnswer()`. Zero model changes.

**Image captions**: Any OCR or captioning model can produce text. That text
flows into the same TF-IDF pipeline.

**Audio transcripts**: Whisper → text → TinyToT. The summarizer handles
long transcripts (podcast summaries, meeting notes) today.

### 3. Translation integration

With [pdf-translate](https://github.com/guilt/pdf-translate) or Google
Translate as a pre-processing step:

```
user query (any language)
  → translate to English
  → TinyToT answers in English
  → translate answer back to user's language
```

No multilingual training. The KB stays in English. Translation is a tool call,
not a learned capability. This makes TinyToT accessible to speakers of any
language with zero additional training.

### 4. Tool calling (already built, easily extended)

The tool-calling architecture is in `tinytot/tools.py`. Pattern detection
→ tool invocation → result injection. Currently supports web search and
encyclopedia lookup. Adding a new tool:

1. Add pattern to `data/categories/tool_calling.md`
2. Register tool schema in the chat request
3. Tool result flows back through the same dispatch pipeline

**Possible tools**: Calculator API, weather API, stock API, code execution
sandbox, database query, CRM lookup, document store search.

### 5. Domain-specific composition heads (30–50M params)

The one thing TinyToT genuinely can't do without a small neural component:
**synthesis** — combining retrieved facts into fluent multi-sentence paragraphs.

The path: train a tiny seq2seq model (T5-small, 60M params) on:
- Input: retrieved passage(s) + query
- Output: synthesised paragraph

This model doesn't need to store facts (TinyToT handles that). It only
needs to compose. At 60M parameters it fits in 240MB, runs on CPU, and can
be trained in hours on a single GPU.

### 6. Continuous learning from agent interactions (Hermes bridge)

`tinytot/content.py` already parses Hermes Learning Journal format:

```
## learning-entry-title
> source: agent-id · session-id · hash: <sha256>
content of what the agent learned
```

Every time a Hermes agent encounters a new fact or pattern, it writes to
a journal file. TinyToT ingests that file on restart. The model learns
from agent experience without retraining.

### 7. Real-time knowledge from structured data

TinyToT's knowledge base is static files. But the retrieval pipeline can
query any key-value store at inference time:

```python
def findKnowledgeAnswer(prompt, knowledgeDir=KNOWLEDGE_DIR):
    # Current: TF-IDF over static files
    # Future: also query Redis / Elasticsearch / vector DB for live data
    static_hit = _staticSearch(prompt, knowledgeDir)
    live_hit = _liveSearch(prompt)  # add this
    return best_of(static_hit, live_hit)
```

This would give TinyToT access to real-time product catalogs, account data,
pricing tables — anything that can be expressed as passages.

### 8. Structured output guarantees

Currently format instructions ("reply with JSON") are handled by the
`json_scoring` mode. But arbitrary structured output (YAML, tables, XML)
requires adding:

1. Format detection patterns in `detectResponseMode()`
2. Template instantiation: query → structured output template → filled output

This is deterministic and testable — the model always produces valid JSON
because it fills a template, not because it "learned" JSON syntax.

---

## The thesis in one sentence

TinyToT demonstrates that ~60% of LLM parameters store facts that could
instead live in text files — and the remaining ~40% (the composition mechanism)
needs only ~30–50M parameters, not 7B, to be practical.

The current system proves this for factual recall, arithmetic, and code
generation. The path to proving it for synthesis is a 60M-parameter composition
head trained on retrieved-then-composed examples — not a 70B model trained on
the entire internet.
