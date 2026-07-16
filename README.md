# TinyToT — Tree of Thoughts Inference Server

[![PyPI](https://img.shields.io/pypi/v/tinytot)](https://pypi.org/project/tinytot/)
[![GitHub](https://img.shields.io/badge/github-guilt/tinytot-blue)](https://github.com/guilt/tinytot)

A local, privacy-first inference server that answers questions, reasons, generates
code, handles documents, and holds natural multi-turn conversations —
**with no model weights, no GPU, and no network required.**

Fully Ollama-compatible and Hermes drop-in (`/v1/chat/completions`).

---

## The core idea

Every large language model above 1B parameters does two completely different things:

1. **Fact storage** — billions of facts memorised in FFN weight matrices (~1–4 bits/param)
2. **Composition** — combining retrieved facts into coherent answers

TinyToT separates these. Facts live in plain markdown files. The retrieval engine is a
**five-head TF-IDF index with BM25 re-ranking** — zero learnable parameters, instant
updates, no training. The only part that would genuinely need parameters is open-ended
generation, and as Phi-1 and DistilBERT research shows, that requires ~30–50M
parameters — not 7B, not 70B.

---

## Benchmark results

| Benchmark | Score | Notes |
|---|---|---|
| Routing accuracy | **53/53 (100%)** | 15 domain categories |
| Knowledge retrieval precision | **15/15 (100%)** | Direct factual Q&A |
| Novel reasoning (held-out) | **18/18 (100%)** | Paraphrased — no training-string match |
| Novel routing (unseen phrasings) | **22/22 (100%)** | Router generalisation |
| Novel math (random seeds) | **25/25 (100%)** | Anti-cheat: random numbers each run |
| Code generation | **49/50 (98%)** | 7 languages, 648 templates |
| Summarization | **11/11 (100%)** | Multi-domain extractive |
| Terminal tasks | **7/7 (100%)** | Shell + file + data tools |
| Agent tools | **10/10 (100%)** | File, data, shell, web, search, media |
| Real-world image analysis | **5/5 (100%)** | Pillow-based pixel + text analysis |
| Real document extraction | **5/5 (100%)** | PDF, DOCX, CSV, Markdown |
| Video/GIF analysis | **3/3 (100%)** | Duration, FPS, keyframes |
| Game24 | **20/20 (100%)** | 24-game solver |
| Creative writing (ToT) | **5/5 (100%)** | Story continuation, haiku |
| Multimodal reasoning | **5/5 (100%)** | Image → ToT reasoning chain |
| SWE-lite | **10/10 (100%)** | Bug diagnosis from error traces |

---

## Capabilities

### 1. Factual Q&A — 30+ knowledge domains
Plain `.md` files in `tinytot/_data/knowledge/`. Drop a file, restart, done.
- Physics, chemistry, biology, medicine, law, macroeconomics, psychology
- Earth science, geography/geopolitics, world history
- Computer science, software engineering, technology & society
- Finance, investing, mathematics

### 2. Compute engine — exact answers, no retrieval
Handles a wide class of problems through direct computation:

| Capability | Example | Answer |
|---|---|---|
| Arithmetic | `347 × 18` | `6246` |
| Algebra | `3x + 7 = 22` | `5` |
| Geometry | `Volume of sphere radius 4` | `268` |
| Percentages | `$120 discounted 25% then taxed 8%` | `$97.20` |
| Unit conversion | `32°F to Celsius` | `0°C` |
| Multi-leg distance | `60mph for 2.5h then 80mph for 1.5h` | `270` |
| Work rate | `A finishes in 3h, B in 6h. Together?` | `2h` |
| Structured data | `Alice=85, Bob=92, Carol=78. Highest?` | `Bob (92)` |
| Fraction of total | `12 slices, Alice ate 3, Bob 4, Carol rest` | `5/12` |
| Logic deduction | `All mammals warm-blooded. Dolphins?` | `Yes` |
| Transitive relations | `John taller than Mary, Mary taller than Bob` | `John taller than Bob` |
| Propositional logic | `A implies B, B implies C, A is true` | `C is true` |
| Coreference | `Alice told Bob she was leaving. Who?` | `Alice` |
| Contradiction | `'All birds fly' vs 'Penguins cannot fly'` | `Contradiction` |
| Date reasoning | `Days between 2024-01-01 and 2024-03-15` | `74` |
| Letter counting | `How many r's in strawberry?` | `3` |

### 3. Use-case handlers — 10 GenAI workloads
Data-driven dispatch via `tinytot/_data/generate/` YAML files:

| Handler | Example prompt |
|---|---|
| `rewrite` | "Make this more formal: hey wanna grab lunch?" |
| `extract` | "Extract all emails from this text: ..." |
| `table` | "Compare Python and JavaScript in a table" |
| `brainstorm` | "Give me 5 ideas for a mobile app" |
| `debug_inline` | "This code has a bug: for i in range(10) print(i)" |
| `rewrite_code` | "Rewrite this in a more Pythonic way: ..." |
| `howto` | "How do I set up a Python project?" |
| `uncertainty` | "Will the stock market go up tomorrow?" |
| `multidoc` | "Doc1 says X. Doc2 says Y. What do they agree on?" |
| `creative` | "Write a haiku about autumn" |

All patterns, substitutions, templates, and guides live in YAML — **no code changes to extend**.

### 4. Code generation — 648 templates, 7 languages
Pattern → template matching via `tinytot/_data/codegen/patterns.yaml`.
Multi-file project scaffolding via `tinytot/_data/codegen/projects.yaml`:

| Blueprint | What it generates |
|---|---|
| `flask_api` | app.py + tests + requirements.txt + README |
| `fastapi_api` | main.py + Pydantic models + tests + README |
| `python_cli` | cli.py + argparse subcommands + tests + README |
| `data_pipeline` | pipeline.py + ETL scaffold + tests + README |
| `python_package` | src layout + pyproject.toml + tests + README |

### 5. Multi-turn refinement
With conversation history, TinyToT applies 10 code transformations to prior responses:
`make_async`, `add_types`, `add_error_handling`, `add_logging`, `add_docstring`,
`simplify`, `optimize`, `translate`, `add_tests`, `explain`.

### 6. Code explanation (AST-based)
Paste any Python code — TinyToT parses it with `ast` and reports:
classes, methods, attributes, function signatures, loop/branch counts,
recursion detection, O(n²) warnings.

### 7. Agentic tools — 11 tools, fully local
- `WebTool`, `SearchTool`, `DocumentTool` (PDF, DOCX, TXT, Markdown)
- `TranslateTool` (googletrans / Google free endpoint / MyMemory; optional `pip install tinytot[translation]` for offline ctranslate2)
- `DataTool`, `FileTool`, `ShellTool`
- `ImageTool`, `VideoTool`, `AudioTool`, `MediaFetchTool` (yt-dlp)

### 8. Multilingual — 24 languages
Time-aware greetings, polyglot conversation, offline translation.
Auto-detects CJK, Arabic, Hangul, Cyrillic scripts.

### 9. Multi-headed retrieval (5 heads)
- H1: TF-IDF unigrams (standard)
- H2: TF-IDF on conclusion text only
- H3: Character trigram (sub-word, typo-robust)
- H4: BM25 (TF saturation + length normalisation)
- H5: Keyword frontmatter exact match
Two-stage: O(N) coarse TF-IDF scan → multi-head re-rank on top-20.

### 10. Conversational features
- Contraction normalisation (`what's` → `what is`)
- Clarification on ambiguous short prompts
- Conversation history context (follow-ups, elaboration requests)

---

## Quick start

```bash
# Quick start (end user)
pip install tinytot
tinytot                      # starts on port 11434

# Development (from repo)
make install
make run
```

---

## Test it

```bash
# 1. Start the server
tinytot

# 2. Query from the command line
curl http://localhost:11434/api/generate \
  -d '{"model":"tinytot","prompt":"What is 15% of 240?","stream":false}'

# 3. Use with opencode (AI coding CLI)
opencode run -m ollama/tinytot "Write a binary search in Python"
# → opencode.json at repo root configures TinyToT as the Ollama provider.
#   All inference runs locally — no API keys, no GPU, no network needed.
```

---

## Usage

TinyToT is a drop-in replacement for Ollama and a Hermes-compatible backend.

```bash
# Factual Q&A
curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","messages":[{"role":"user","content":"What causes earthquakes?"}],"stream":false}'

# Compute
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"A product costs $120, discounted 25%, then taxed 8%. Final price?","stream":false}'
# → "$97.20 (−25% discount: $120 × 0.75 = $90; +8% tax: $90 × 1.08 = $97.20)"

# OpenAI-compatible (for Hermes and other clients)
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","messages":[{"role":"user","content":"Write a haiku about autumn"}]}'

# Multi-turn refinement
# Turn 1: get code
# Turn 2: "make it async" → applies async transformation to prior code block

# Project scaffolding
curl http://localhost:11434/api/generate \
  -d '{"model":"tinytot","prompt":"Build a Flask REST API with a users endpoint"}'
# → generates app.py + tests + requirements.txt + README in a single response
```

---

## Self-replication (NanoToT variants)

TinyToT can clone itself with an optional delta knowledge set, enabling lightweight
domain-specific variants (`nanotot-dino`, `nanotot-bird`, etc.) that share the same
Python package but carry different knowledge files.

```bash
# Clone with no extra knowledge (exact copy)
tinytot-clone ~/nanotot-dino

# Clone with additional domain knowledge layered on top
tinytot-clone ~/nanotot-dino --extra-knowledge dino.md reptiles.md

# Run the clone (TINYTOT_DATA_DIR overrides the bundled data directory)
TINYTOT_DATA_DIR=~/nanotot-dino tinytot
```

From Python:

```python
from tinytot.clone import clone

dest = clone("~/nanotot-bird", extra_knowledge=["birds.md"])
# → ~/nanotot-bird/_data/ with birds.md merged into knowledge/
print(f"Run with: TINYTOT_DATA_DIR={dest} tinytot")
```

Delta files with the same stem as existing knowledge files replace them.
The Python source (`pip install tinytot`) is shared across all variants.

---

## Extending TinyToT — everything is data

| To add... | Edit this file | Code change? |
|---|---|---|
| New factual knowledge | `tinytot/_data/knowledge/<domain>.md` | No |
| New reasoning category | `tinytot/_data/categories/<domain>.md` | No |
| New code template | `tinytot/_data/codegen/templates/<key>.md` + `patterns.yaml` | No |
| New project blueprint | `tinytot/_data/codegen/projects.yaml` | No |
| New how-to guide | `tinytot/_data/generate/howto_scripts.yaml` | No |
| New static code check | `tinytot/_data/generate/static_checks.yaml` | No |
| New haiku topic | `tinytot/_data/generate/creative/haiku_topics.yaml` | No |
| New story template | `tinytot/_data/generate/creative/story_templates.yaml` | No |
| New use-case handler | `tinytot/_data/generate/use_cases.yaml` + handler fn | Minimal |
| New comparative adjective | `tinytot/_data/generate/comparatives.yaml` | No |
| New contradiction pair | `tinytot/_data/generate/contradiction_pairs.yaml` | No |
| New gendered name | `tinytot/_data/generate/names_gender.yaml` | No |

---

## Knowledge base

```bash
# Add knowledge
echo "## My Domain

The key fact is X. Context goes here." >> tinytot/_data/knowledge/my_domain.md

# Restart the server — no build step, no retraining
tinytot        # or: make run
```

Each paragraph becomes a separate searchable passage.
The Hermes bridge: drop any Hermes Learning Journal (`yyyy-mm-dd.md`) into
`tinytot/_data/knowledge/` and it becomes immediately retrievable.

---

## Document handling

Dependencies for PDF, Word, Excel, PowerPoint, XML, and JSON streaming are
included — installed automatically with `pip install tinytot` or `make install`.

| Library | Format | Status |
|---|---|---|
| `pypdf` | PDF | ✅ `DocumentTool` agent |
| `python-docx` | Word (.docx) | ✅ `DocumentTool` agent |
| `openpyxl` | Excel (.xlsx) | ✅ how-to guides in YAML |
| `python-pptx` | PowerPoint (.pptx) | ✅ how-to guides in YAML |
| `lxml` | XML / HTML | ✅ how-to guides in YAML |
| `ijson` | JSON streaming | ✅ how-to guides in YAML |
| `tabulate` | Table rendering | ✅ |

How-to guides for chunked CSV, Excel reading/filtering, JSON streaming,
recursive JSON key extraction, and CSV→JSON conversion are in
`tinytot/_data/generate/howto_scripts.yaml`.

---

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/generate` | POST | Ollama-compatible text generation |
| `/api/chat` | POST | Ollama-compatible chat with history + tool support |
| `/api/tags` | GET | List available models |
| `/api/show` | POST | Model details |
| `/api/pull` | POST | No-op (compatibility) |
| `/api/quit` | POST/GET | Graceful shutdown |
| `/v1/chat/completions` | POST | OpenAI-compatible (Hermes drop-in) |
| `/v1/models` | GET | OpenAI model list |
| `/api/agent` | POST | Plan-execute-synthesise agentic loop |
| `/api/agent/tools` | GET | List registered tools |
| `/api/agent/tool` | POST | Run a single tool by name |
| `/api/agent/learn` | POST | Write to Hermes Learning Journal |
| `/api/summarize` | POST | Extractive document summarization |

---

## Development

```bash
make tests        # pytest with coverage (gate ≥ 80%)
make unit-tests   # unit tests only
make lint         # ruff check
make format       # ruff format
make precommit    # run all pre-commit hooks (16 benchmarks + tests + lint)
make docs         # regenerate API docs + build Sphinx HTML
make docs-serve   # serve docs on localhost
make live-docs    # live-reload docs server
make benchmark    # ingest corpora then run all benchmarks (alias: make bench)
make build        # build wheel
make build-binary # build self-contained binary (dist/tinytot or dist/tinytot.exe)
```

Pre-commit runs automatically on every commit:
ruff → ruff-format → mypy → pytest → benchmark regression guard (16 benchmarks)

---

## Project structure

```
tinytot/
  inference.py      dispatch: normalise → refine → project → use-case →
                    compute → social → agent → knowledge → codegen → ToT
  retrieval.py      5-head TF-IDF index + BM25 re-ranker
  compute.py        AST-safe arithmetic, logic, coreference, structured data
  generate.py       10 use-case handlers (all content in _data/generate/)
  refine.py         multi-turn code refinement, AST code explanation
  codegen.py        648-template code generation + 5-blueprint project scaffolding
  content.py        chain/category/knowledge loading (all lru_cached)
  agent.py          PlanExecuteLoop, LearningJournal, detectAgentNeeds
  tools_ext.py      11-tool registry (web, doc, translate, data, file, shell, AV)
  lang.py           Lang enum, 24 languages, SOCIAL_PATTERN, detect_lang()
  server.py         FastAPI app, Ollama + OpenAI endpoints
  ingest.py         IngestSource ABC — GSM8K, Princeton ToT, argostranslate packs
  benchmark.py      16 benchmarks including 3 anti-cheat (novel math/reasoning/routing)
  summarize.py      extractive summarization
  clone.py          self-replication — tinytot-clone CLI, NanoToT delta variants
  _web/             Web UI (index.html served at /, style.css)
  cli/              CLI tools (generate_api_docs)

  _data/            bundled package data (ships inside the wheel)
    knowledge/        30+ markdown knowledge files, 15,000+ passages
    categories/       15 domain reasoning-chain files
    codegen/
      templates/      648 algorithm templates (7 languages each)
      patterns.yaml   regex → template key
      decompositions.yaml  compositional problem decompositions
      projects.yaml   5 multi-file project blueprints
      config.yaml     language detection patterns
    generate/
      use_cases.yaml       10 use-case detection patterns
      rewrite_subs.yaml    38 formality/casualness substitutions
      extractors.yaml      8 entity regex extractors
      static_checks.yaml   19 static code analysis patterns
      pythonic_subs.yaml   10 Pythonic rewrite transforms
      howto_scripts.yaml   15+ step-by-step how-to guides
      uncertainty.yaml     15 unknowable-topic keywords
      contradiction_pairs.yaml  20 polarity opposition pairs
      names_gender.yaml    40 gendered first names
      comparatives.yaml    31 comparative adjectives
      creative/
        haiku_topics.yaml       18 topic word-banks
        story_templates.yaml    8 story continuation templates
    eval/
      summarize_eval.md    11-domain summarization benchmark cases
    schema/
      information_patterns.md  tool dispatch patterns
    .sources/         runtime clones (gitignored, populated by tinytot-ingest)
    journal/          agent learning journal (gitignored, runtime per-machine)
```

Override the data directory at runtime for NanoToT variants:
```bash
TINYTOT_DATA_DIR=/path/to/delta-data tinytot
```

---

## Links

- **PyPI**: [pypi.org/project/tinytot](https://pypi.org/project/tinytot/)
- **GitHub**: [github.com/guilt/tinytot](https://github.com/guilt/tinytot)

## License

MIT — see [LICENSE.md](LICENSE.md).
