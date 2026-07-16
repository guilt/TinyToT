# TinyToT User Guide

## Where to start

| I want to... | Section |
|---|---|
| Get up and running in 5 minutes | [Quick Start](#quick-start) |
| Understand the architecture | [How a query is answered](#how-a-query-is-answered) |
| Add facts / domain knowledge | [Knowledge base](#knowledge-base) |
| Use arithmetic, algebra, logic | [Compute engine](#compute-engine) |
| Generate code or a project | [Code generation](#code-generation) |
| Rewrite, extract, debug, brainstorm | [Use-case handlers](#use-case-handlers) |
| Work with documents (PDF, Excel…) | [Document handling](#document-handling) |
| Use agentic tools | [Agent tools](#agent-tools) |
| Use from Hermes / OpenAI clients | [API endpoints](#api-endpoints) |
| Run benchmarks | [Benchmarking](#benchmarking) |
| Extend TinyToT | [Everything is data](#everything-is-data) |

---

## How a query is answered

Every prompt passes through this pipeline. The first stage that produces an
answer wins — later stages never run.

```
prompt
  │
  ├─ 0a. normalise           expand contractions (what's → what is)
  ├─ 0b. multi-turn refine   "make it async" → apply to prior code in history
  ├─ 0c. project scaffold    "build a Flask API" → multi-file project
  ├─ 0d. use-case handler    rewrite / extract / table / debug / howto / creative …
  ├─ 1.  json_scoring        "reply with json"  →  {"score":…,"rationale":…}
  ├─ 2.  summarize           "summarize in N words"  →  extractive summary
  ├─ 3.  compute             arithmetic, logic, structured data  →  exact result
  ├─ 4.  social              hello / how are you  →  conversational response
  ├─ 5.  agent               URL / file path / "search for"  →  tool pipeline
  ├─ 6.  live data           "current weather", "stock price"  →  honest refusal
  ├─ 7.  knowledge base      short factual query  →  passage from data/knowledge/
  ├─ 8.  code generation     "write a binary search"  →  fenced code block
  └─ 9.  reasoning trace     default  →  Tree of Thoughts chain
```

---

## Quick start

```bash
# Quick start (end user)
pip install tinytot
tinytot                       # starts on port 11434

# Development (from repo)
git clone <repo-url>
cd TinyToT
make install
make run
make stop
```

---

## Knowledge base

Facts live in plain markdown files in `data/knowledge/`. Each paragraph is a
separate searchable passage.

```markdown
## My Domain

The key fact about this topic is X. Context goes here.

A second paragraph covers a related subtopic.
```

**Retrieval thresholds:**
- Score ≥ 0.65: passage returned directly as the answer.
- Score ≥ 0.25: passage used as grounding context in the reasoning chain.
- Score < 0.20: chain runs ungrounded.

**Five-head retrieval:** H1 TF-IDF unigrams, H2 conclusion-text TF-IDF,
H3 character trigrams, H4 BM25, H5 keyword frontmatter exact match.
Two-stage: O(N) coarse scan → multi-head re-rank on top-20.

---

## Compute engine

TinyToT solves the following exactly — no retrieval, no generation:

| Category | Examples |
|---|---|
| Arithmetic | `347 * 18`, `sqrt(144)`, `12\!` |
| Algebra | `3x + 7 = 22` → `x = 5` |
| Percentages | `$120 discounted 25% then taxed 8%` → `$97.20` |
| Unit conversion | `72°F to Celsius`, `5 miles to km` |
| Multi-leg distance | `60mph for 2.5h then 80mph for 1.5h` → `270` |
| Fractions of total | `12 slices, Carol ate the rest` → `5/12` |
| Structured data | `Alice=85, Bob=92, Carol=78. Highest?` → `Bob (92)` |
| Transitive logic | `John taller than Mary, Mary taller than Bob` |
| Propositional logic | `A implies B, B implies C, A is true` → `C is true` |
| Coreference | `Alice told Bob she was leaving. Who?` → `Alice` |
| Contradiction | `'All birds fly' vs 'Penguins cannot fly'` → `Contradiction` |
| Letter counting | `How many r's in strawberry?` → `3` |

All via Python `ast` — never calls `eval()` or `exec()`.

---

## Code generation

### Single-file templates (648 templates, 7 languages)
`data/codegen/patterns.yaml` maps regex patterns to template keys.
`data/codegen/templates/<key>.md` contains the code in `## python`, `## javascript`, etc. sections.

### Multi-file project scaffolding
`data/codegen/projects.yaml` defines project blueprints:

| Blueprint | Generates |
|---|---|
| `flask_api` | app.py + tests + requirements.txt + README |
| `fastapi_api` | main.py + Pydantic models + tests + README |
| `python_cli` | cli.py + argparse subcommands + tests + README |
| `data_pipeline` | pipeline.py + ETL scaffold + tests + README |
| `python_package` | src layout + pyproject.toml + tests + README |

### Multi-turn refinement
With conversation history, follow-up prompts transform prior code:
`make_async`, `add_types`, `add_error_handling`, `add_logging`, `add_docstring`,
`simplify`, `optimize`, `translate`, `add_tests`, `explain`.

---

## Use-case handlers

Ten handlers, all content in `data/generate/` YAML files:

| Handler | Trigger examples | Data file |
|---|---|---|
| `rewrite_code` | "Make this Pythonic" | `pythonic_subs.yaml` |
| `rewrite` | "Make this more formal" | `rewrite_subs.yaml` |
| `extract` | "Extract all emails from..." | `extractors.yaml` |
| `table` | "Compare X and Y in a table" | — |
| `brainstorm` | "Give me 5 ideas for..." | — |
| `debug_inline` | "This code has a bug" | `static_checks.yaml` |
| `howto` | "How do I read a large CSV?" | `howto_scripts.yaml` |
| `uncertainty` | "Will the stock market go up?" | `uncertainty.yaml` |
| `multidoc` | "Doc1 says X. Doc2 says Y..." | `contradiction_pairs.yaml` |
| `creative` | "Write a haiku about autumn" | `creative/*.yaml` |

Add a new how-to guide: append to `howto_scripts.yaml`. No code change.

---

## Document handling

Dependencies installed with `make install`:

| Library | Format |
|---|---|
| `pypdf` | PDF |
| `python-docx` | Word (.docx) |
| `openpyxl` | Excel (.xlsx) |
| `python-pptx` | PowerPoint (.pptx) |
| `lxml` | XML, HTML |
| `ijson` | JSON streaming |
| `tabulate` | Tabular data rendering |

How-to guides for chunked CSV, Excel, JSON streaming, and recursive JSON
key extraction are in `data/generate/howto_scripts.yaml`.

---

## Agent tools

11 tools in `tinytot/tools_ext.py`, triggered automatically when the prompt
contains a URL, file path, or agent keyword:

`WebTool`, `SearchTool`, `DocumentTool` (PDF, DOCX, TXT, Markdown),
`TranslateTool` (googletrans / Google free endpoint / MyMemory; optional offline
ctranslate2 via `pip install tinytot[translation]`), `DataTool`, `FileTool`,
`ShellTool`, `ImageTool`, `VideoTool`, `AudioTool`, `MediaFetchTool` (yt-dlp).

---

## API endpoints

| Endpoint | Method | Description |
|---|---|---|---|
| `/api/generate` | POST | Ollama-compatible text generation |
| `/api/chat` | POST | Ollama chat + multi-turn history + tool support |
| `/api/tags` | GET | List available models |
| `/api/show` | POST | Model details |
| `/api/pull` | POST | No-op (compatibility) |
| `/api/quit` | POST/GET | Graceful shutdown |
| `/v1/chat/completions` | POST | OpenAI-compatible (Hermes drop-in) |
| `/v1/models` | GET | OpenAI model list |
| `/api/agent` | POST | Plan-execute-synthesise loop |
| `/api/agent/tools` | GET | List registered tools |
| `/api/agent/learn` | POST | Write to Hermes Learning Journal |
| `/api/summarize` | POST | Extractive summarization |

---

## Benchmarking

```bash
make bench    # all 16 benchmarks with anti-cheat
```

| Benchmark | Baseline |
|---|---|---|
| routing | 53/53 |
| retrieval | 15/15 |
| summarization | 11/11 |
| codegen | 49/50 |
| novel_math | 25/25 |
| novel_reasoning | 18/18 |
| novel_routing | 22/22 |
| terminal | 7/7 |
| agent-tools | 10/10 |
| image-real | 5/5 |
| document-real | 5/5 |
| video-real | 3/3 |
| multimodal | 5/5 |
| game24 | 20/20 |
| tot-text | 5/5 |
| swe-lite | 10/10 |
| translate-real | 8/8 |

The pre-commit hook rejects commits that drop below baseline.

---

## Everything is data

| To add... | Edit | Code change? |
|---|---|---|---|
| New fact | `tinytot/_data/knowledge/<domain>.md` | No |
| New reasoning category | `tinytot/_data/categories/<domain>.md` | No |
| New code template | `tinytot/_data/codegen/templates/<key>.md` + `patterns.yaml` | No |
| New project blueprint | `tinytot/_data/codegen/projects.yaml` | No |
| New how-to guide | `tinytot/_data/generate/howto_scripts.yaml` | No |
| New static code check | `tinytot/_data/generate/static_checks.yaml` | No |
| New haiku topic | `tinytot/_data/generate/creative/haiku_topics.yaml` | No |
| New story template | `tinytot/_data/generate/creative/story_templates.yaml` | No |
| New comparative adjective | `tinytot/_data/generate/comparatives.yaml` | No |
| New contradiction pair | `tinytot/_data/generate/contradiction_pairs.yaml` | No |
| New gendered name | `tinytot/_data/generate/names_gender.yaml` | No |
| New use-case handler | `tinytot/_data/generate/use_cases.yaml` + handler fn | Minimal |

---

## Architecture thesis

TinyToT's central claim: most LLM parameters store facts. Facts don't need parameters.

| Task | TinyToT | Transformer |
|---|---|---|
| Factual recall | ✅ 100%, zero hallucination | ~85–95% |
| Arithmetic | ✅ always exact | ❌ token prediction |
| Logic deduction | ✅ exact solver | ~70–80% |
| Code (known patterns) | ✅ runnable | ✅ but can hallucinate |
| Knowledge update | ✅ edit a text file | ❌ retrain |
| Novel text generation | ❌ no decoder | ✅ |
| Open creative writing | ⚠ template-only | ✅ |
