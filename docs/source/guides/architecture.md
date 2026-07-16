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
through ten stages, first-match-wins:

```{mermaid}
flowchart LR
    P([Prompt]) --> N["0a · Normalise\nclean / expand contractions"]
    N --> R["0b · Multi-turn refine\n10 intents, AST explanation"]
    R --> S["0c · Project scaffold\n5 blueprints from projects.yaml"]
    S --> U["0d · Use-case handler\n10 handlers from use_cases.yaml"]
    U --> J["1 · JSON scoring\n{score, rationale}"]
    J --> SU["2 · Summarize\narc-aware extractive"]
    SU --> C["3 · Compute\nexact arithmetic / logic"]
    C --> SO["4 · Social\ngreeting / small-talk"]
    SO --> A["5 · Agent\ntool-calling loop"]
    A --> L["6 · Live-data guard\nhonest refusal"]
    L --> K["7 · Knowledge base\n5-head retrieval, 24K+ passages"]
    K --> CG["8 · Code generation\n648 templates, 7+ languages"]
    CG --> T["9 · Tree of Thoughts\nmulti-path reasoning"]

    style C fill:#d4edda
    style K fill:#cce5ff
    style CG fill:#fff3cd
    style T fill:#f8d7da
```

Each stage reads from **data files**, not from neural weights.

### The core systems

**Knowledge retrieval** (`tinytot/retrieval.py`)

Two-stage five-head pipeline over `tinytot/_data/knowledge/*.md`. Each paragraph is one
passage.

```{mermaid}
flowchart TD
    Q([Query]) --> TF["Stage 1 · Coarse TF-IDF\ntop-20 candidates"]
    TF --> H1["H1 · TF-IDF unigrams\ntitle + thoughts"]
    TF --> H2["H2 · TF-IDF on conclusion\noutput-space representation"]
    TF --> H3["H3 · Character trigrams\nsub-word, typo-robust"]
    TF --> H4["H4 · BM25\nTF saturation + length norm"]
    TF --> H5["H5 · Keyword match\nfrontmatter exact"]
    H1 & H2 & H3 & H4 & H5 --> RE["Re-rank & score\nbest passage if ≥ 0.65"]
    RE --> ANS([Answer])
```

Q&A-format passages get a 1.15× relevance bonus. Noisy corpora (benchmark Q&A,
fill-in-the-blank) get a 0.6× penalty. Current index: **24,000+ passages** across
30+ domains.

**Compute engine** (`tinytot/compute.py`)

Deterministic solvers for: arithmetic, algebra (linear equations), geometry
(8 formulas), percentages, unit conversion, date arithmetic, word problems,
logical deduction (modus ponens/tollens), propositional logic chains (A→B→C),
coreference resolution, contradiction detection, structured data comparisons,
fraction-of-total, chained percentage calculations, and multi-step word problems.
Never uses token prediction. Results are always exact.

Content (names, comparatives, contradiction pairs) loads from
`tinytot/_data/generate/*.yaml` — no knowledge hardcoded in Python.

**Code generation** (`tinytot/codegen.py`)

Pattern matching (`tinytot/_data/codegen/patterns.yaml`) → template lookup
(`tinytot/_data/codegen/templates/<key>.md`). **648 templates**, 7+ languages (Python,
JavaScript, Go, Rust, Java, Ruby, Swift, TypeScript, C++, C#, SQL, Kotlin,
Bash), 300+ patterns. Language detection and request detection patterns live in
`tinytot/_data/codegen/config.yaml`. Compositional problems are decomposed in
`tinytot/_data/codegen/decompositions.yaml`.

`generateProject()` handles multi-file scaffolding from five blueprints in
`tinytot/_data/codegen/projects.yaml`: `flask_api`, `fastapi_api`, `python_cli`,
`data_pipeline`, `python_package`.

**Use-case handlers** (`tinytot/generate.py`)

Ten structured use-case handlers that fire before the main scoring chain.
All patterns declared in `tinytot/_data/generate/use_cases.yaml`. Supporting data files
in `tinytot/_data/generate/`: `rewrite_subs.yaml`, `extractors.yaml`, `static_checks.yaml`,
`pythonic_subs.yaml`, `howto_scripts.yaml`, `uncertainty.yaml`,
`contradiction_pairs.yaml`, `creative/haiku_topics.yaml`,
`creative/story_templates.yaml`. Adding a new how-to guide or static check
requires only a YAML edit.

**Multi-turn refinement** (`tinytot/refine.py`)

Iterative code improvement across **10 intents** (make_async, add_types,
add_error_handling, add_logging, add_docstring, simplify, optimize, translate,
add_tests, explain). Uses AST-based code parsing for structural awareness.
`explainCode()` reports classes, methods, attributes, loop/branch counts,
recursion detection, and O(n²) warnings.

**Summarization** (`tinytot/summarize.py`)

Arc-aware sentence election: the document is split into narrative arcs
(setup/complication/crisis/resolution), and the best sentence per arc is
elected using: entity density × plot-verb weight × outcome-signal boost ×
IDF score × position boost. Output quality: 11/11 on 11-domain eval.

**Tree of Thoughts** (`tinytot/inference.py`)

Multi-path reasoning over `tinytot/_data/categories/*.md` chains. Each category has up
to 15 chains. The best chain is selected by TF-IDF cosine similarity. Chains
with an explicit `Conclusion:` field return that field directly — no trace
wrapper.

---

## Ingestion pipeline

`IngestSource` is an ABC with three concrete implementations:

- `GSM8KSource` — ingests GSM8K math problems
- `PrincetonToTSource` — ingests Princeton Tree of Thoughts reasoning data
- `ArgostranslateSource` — installs 132 translation pack pairs across 12 languages

24-language support is provided via `lang.py`. Document ingestion libraries
now include `openpyxl` (Excel), `python-pptx` (PowerPoint), `lxml` (XML),
`ijson` (JSON streaming), `tabulate` (table rendering).

---

## Self-replication and variants

TinyToT can clone itself as a minimal delta — a single `variant.yaml` (174 bytes)
that layers a personality over the shared base install.

```{mermaid}
flowchart TD
    BASE["pip install tinytot\nBase install\n24K+ passages · 648 templates"]
    BASE -->|tinytot-clone --variant bird| BIRD["~/nanotot-bird\nvariant.yaml only\n+greeting +emoji"]
    BASE -->|tinytot-clone --variant dino| DINO["~/nanotot-dino\nvariant.yaml only"]
    BASE -->|tinytot-clone --extra-knowledge facts.md| CUSTOM["~/nanotot-custom\nvariant.yaml + knowledge/facts.md"]
    BIRD -->|TINYTOT_DATA_DIR=~/nanotot-bird tinytot| RB["Chirp chirp!\nI'm TinyToT Bird..."]
    DINO -->|TINYTOT_DATA_DIR=~/nanotot-dino tinytot| RD["ROARRR!\nI'm TinyToT Dino..."]
    CUSTOM --> RC["Custom greeting\n+ delta knowledge"]
```

The overlay mechanism (`content.py::loadKnowledgePassages`) merges base + delta
at runtime: delta files override base files with the same stem; new delta files
extend the corpus. No copy of the full dataset is made.

```bash
# Create a bird variant (174 bytes)
tinytot-clone ~/nanotot-bird --variant bird

# Run it
TINYTOT_DATA_DIR=~/nanotot-bird tinytot -p hello
# → Chirp chirp! I'm TinyToT Bird...

# Or start the server
TINYTOT_DATA_DIR=~/nanotot-bird tinytot
```

---

## How it differs from an LLM

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
| **Code generation** | ✅ 648 templates, always runnable | ✅ but can hallucinate APIs |
| **Project scaffolding** | ✅ 5 blueprints, complete multi-file output | ✅ but can omit files |
| **Multi-turn refinement** | ✅ AST-aware, 10 intents | ✅ but can drift |
| **Use-case structured output** | ✅ 10 handlers, template-driven | ✅ but inconsistent |
| **Synthesis** | ❌ returns passages, not new text | ✅ generates novel sentences |
| **Long context** | Limited (extractive summarization) | ✅ full attention window |

---

## Why it requires almost no training

The hard parts of LLM training are:
1. **Fact injection**: forcing facts into weight matrices
2. **Instruction following**: making the model respond as asked
3. **Format compliance**: making output consistently structured

TinyToT solves all three without training:
1. Facts go into `tinytot/_data/knowledge/*.md` (text files, not weights)
2. Instruction following is deterministic dispatch (code, not learned)
3. Format compliance is template instantiation (also code)

What *would* require training: **synthesis** — generating fluent novel
sentences that combine facts in new ways. TinyToT can't write a paragraph
that wasn't in the training data. That requires a ~30–50M parameter
composition head. Everything else it does better without one.

---

## Cost and development benefits

**Zero training cost.** No GPU, no data pipeline, no experiment tracking.

**Zero serving cost.** Runs on a CPU at 126 QPS.

**Zero hallucination on facts.** If a fact isn't in `tinytot/_data/knowledge/`, the model
says so. If it is, it returns the exact passage.

**Instant knowledge update.** Edit a `.md` file, restart (10 seconds).

**Full auditability.** Every answer cites an implicit source. Debugging is `grep`.

**Test-driven development.** All 7 benchmarks run in 30 seconds. Pre-commit
hooks prevent regressions — every commit is gated on the benchmark suite.

---

## Where we can do radically amazing things

### 1. Multi-language code generation (currently: 7+ languages)

Every language is just a `## <language>` section in a `.md` file. Adding
any new language to all 648 templates is a data project, not a code project.

### 2. Multi-modal input (documents, images, audio)

`openpyxl`, `python-pptx`, `lxml`, and `ijson` are already installed. The
retrieval pipeline doesn't care about source format — it needs tokenized text.
PDF extraction already works via `DocumentTool`.

### 3. Translation integration

Argostranslate (integrated via `ArgostranslateSource`) supports 24 languages.
The KB stays in English; translation is a tool call, not a learned capability.

### 4. Tool calling (already built)

The tool-calling architecture is in `tinytot/tools.py`. Adding a new tool:

1. Add pattern to `tinytot/_data/categories/tool_calling.md`
2. Register tool schema in the chat request
3. Tool result flows back through the same dispatch pipeline

### 5. Domain-specific composition heads (30–50M params)

The one thing TinyToT can't do without a small neural component: **synthesis**.

Path: train a T5-small (60M params) on retrieved passage(s) + query → synthesised
paragraph. This model doesn't store facts — TinyToT handles that. At 60M params
it fits in 240MB, runs on CPU, trains in hours on a single GPU.

### 6. Continuous learning from Hermes

Every time a Hermes agent learns a new fact, it writes a journal file. TinyToT
ingests that on restart. The model learns from agent experience without retraining.

### 7. Real-time knowledge

The retrieval pipeline can query any key-value store at inference time alongside
static files — product catalogs, account data, pricing tables, anything that
can be expressed as passages.

---

## The thesis in one sentence

TinyToT demonstrates that ~60% of LLM parameters store facts that could instead
live in text files — and the remaining ~40% (composition) needs only ~30–50M
parameters, not 7B, to be practical.

The current system proves this for factual recall, arithmetic, logic, code
generation, multi-turn refinement, and structured use-case handling. The path to
synthesis is a 60M-parameter composition head — not a 70B model trained on the
entire internet.
