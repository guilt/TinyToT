# Getting Started with TinyToT

Welcome. This guide gets you from zero to your first query in under 5 minutes.

## Prerequisites

- Python 3.8+
- `pipenv` installed


## Installation

```bash
git clone <repository-url>
cd TinyToT
make pre-check    # verify Python version
make install      # creates pipenv venv, installs all deps
```

## Start the server

```bash
make run
# INFO: Uvicorn running on http://0.0.0.0:11434
```

TinyToT starts on port 11434 — the same port as Ollama. Any Ollama-compatible
client works immediately.

## Your first queries

**Factual recall** — answered directly from the knowledge base:

```bash
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"What is the capital of France?","stream":false}'
# → "Paris"
```

**Arithmetic** — handled by the compute engine, never by pattern matching:

```bash
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"What is 347 * 18?","stream":false}'
# → "6246"
```

**Code generation** — returns runnable code in the requested language:

```bash
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"Write a Python function to reverse a string","stream":false}'
# → ```python
#    def reverse_string(s: str) -> str:
#        return s[::-1]
#    ```
```

**Summarization** — extractive summary of any long text:

```bash
curl http://localhost:11434/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"document":"<full text here>","max_words":50}'
```

**Live data** — honest refusal when real-time data would be needed:

```bash
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"What is the current weather in Tokyo?","stream":false}'
# → "I don't have access to live or real-time data..."
```

## Stop the server

```bash
make stop
```

## Run benchmarks

```bash
make bench
```

Runs all 8 benchmarks — routing, retrieval, truthfulqa, summarization, code
generation, novel_math, novel_reasoning, and novel_routing — and prints ASCII
bar charts. Takes about 30 seconds. The same benchmarks run automatically as a
pre-commit regression guard.

## Quick reference

```
make run              start server (port 11434)
make stop             graceful shutdown
make tests            pytest with coverage
make unit-tests       unit tests only
make lint             ruff check
make format           ruff format
make precommit        pre-commit checks (runs all 8 benchmarks)
make benchmark        ingest corpora then run all 8 benchmarks (alias: make bench)
make docs             regenerate API docs + build Sphinx HTML
make docs-serve       serve built docs on localhost
make live-docs        live-reload docs server
make build            build wheel
```

## How a query is answered

Every prompt goes through this dispatch pipeline (first match wins):

```{mermaid}
flowchart TD
    P([Prompt]) --> N["0a · Normalise"]
    N --> R["0b · Multi-turn refine\n10 intents, AST explanation"]
    R --> S["0c · Project scaffold\n5 blueprints"]
    S --> U["0d · Use-case handler\n10 handlers"]
    U --> J["1 · JSON scoring"]
    J --> SU["2 · Summarize"]
    SU --> C["3 · Compute\nexact numeric / logical"]
    C --> SO["4 · Social\ngreeting / variant greeting"]
    SO --> A["5 · Agent\ntool dispatch"]
    A --> L["6 · Live-data guard"]
    L --> K["7 · Knowledge base\n5-head retrieval"]
    K --> CG["8 · Code generation\n648 templates"]
    CG --> T["9 · Tree of Thoughts"]
```

See [Core Concepts](guides/concepts.md) for why each stage exists and
[How-To: Ingesting Corpora](how_to/08_ingesting_corpora.md) for how to feed
new data into the knowledge and codegen stages.

## What's next

| I want to... | Guide |
|---|---|
| Understand the architecture | [Core Concepts](guides/concepts.md) |
| Add facts / domain knowledge | [How-To: Knowledge Base](how_to/01_knowledge_base.md) |
| Add arithmetic / logic | [How-To: Compute Engine](how_to/02_compute_engine.md) |
| Add reasoning chains | [How-To: Reasoning Chains](how_to/03_reasoning_chains.md) |
| Add code templates | [How-To: Code Generation](how_to/10_code_generation.md) |
| Connect external tools | [How-To: Tool Calling](how_to/04_tool_calling.md) |
| Ingest datasets | [How-To: Ingesting Corpora](how_to/08_ingesting_corpora.md) |
| Measure performance | [How-To: Benchmarking](how_to/07_benchmarking.md) |
| Extend TinyToT | [How-To: Extending](how_to/09_extending.md) |

## Termux / Android

TinyToT runs on Android/Termux (including inside proot). A few packages have no
PyPI wheels for Termux's `android_30_arm64_v8a` platform tag, so pip falls back
to source builds. The repository ships the tooling needed to make that work:

### Reuse an existing venv with pipenv and make

```bash
# One-time: create a venv that shares the (already-provisioned) system packages
python3 -m venv --system-site-packages .venv

# Copy the local override template and set:
#   PYTHON_VERSION ?= 3.13
#   export PIPENV_VENV_IN_PROJECT = 1
cp Makefile.user.template Makefile.user   # then edit as above

make run          # starts the server on :11434
make docs         # regenerates API docs + builds HTML
make tests        # full pytest suite
make precommit    # ruff + pytest + data-quality + benchmark guards
```

`pipenv run` never installs anything, so the daily targets stay fast. Only
`make install` syncs the full `Pipfile`.

### Native wheels that need a manual build

`pydantic-core` and `rpds-py` are Rust crates with no `android_30_arm64_v8a`
wheel; a source build through pip fails because build-isolation tries to
compile `maturin` first. Build them once with the cargo-installed maturin and
drop the wheels into `~/WS/Wheels`:

```bash
cargo install maturin --locked
cd <pydantic-core checkout> && ./scripts/build-android.sh   # → ~/WS/Wheels/
python3 -m pip install ~/WS/Wheels/pydantic_core-*.whl ~/WS/Wheels/rpds_py-*.whl
```

`Pillow` should be installed from the Termux package repository (the PyPI
source build links glibc's `libc.so.6`, which bionic cannot load):

```bash
pkg install python-pillow
```

### Go toolchain (codegen execution tests)

Termux's `golang` package ships a trimmed `go` binary. Under proot it needs
`GOROOT` exported and `-e` as the first argument; the detection-based wrapper
in `~/WS/DotFiles/bin/go` applies only when the plain invocation fails:

```bash
cp ~/WS/DotFiles/bin/go $PREFIX/bin/go   # re-apply after `pkg upgrade golang`
```
