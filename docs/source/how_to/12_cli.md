# How-To: CLI (Non-Interactive Mode)

TinyToT ships with a command-line interface for single-shot queries, scripting,
and variant testing — no server required.

---

## Usage

```
tinytot [-p PROMPT] [--host HOST] [--port PORT]
```

| Flag | Description |
|---|---|
| *(no flags)* | Start the HTTP server on port 11434 |
| `-p PROMPT` | Run a single prompt, print the response, exit |
| `--prompt PROMPT` | Same as `-p` |
| `--port PORT` | Override server port (default: 11434) |
| `--host HOST` | Override server host (default: 0.0.0.0) |

---

## Examples

**Factual query:**

```bash
tinytot -p "What causes earthquakes?"
# → Earthquakes are caused by the movement of tectonic plates...
```

**Arithmetic:**

```bash
tinytot -p "347 * 18"
# → 6246
```

**Code generation:**

```bash
tinytot -p "Write a Python function to reverse a linked list"
```

**Variant greeting:**

```bash
TINYTOT_DATA_DIR=~/nanotot-dino tinytot -p hello
# → ROARRR! I'm TinyToT Dino — 65 million years of knowledge (and counting)...
```

**Piping:**

```bash
echo "What is the boiling point of water?" | xargs -I{} tinytot -p "{}"
# → The boiling point of water is 100°C (212°F) at standard atmospheric pressure.
```

**Scripting:**

```bash
#!/bin/bash
for domain in physics chemistry biology; do
  echo "=== $domain ==="
  tinytot -p "Give me a key fact about $domain"
done
```

---

## Starting the server

```bash
# Default (port 11434, all interfaces)
tinytot

# Custom port
tinytot --port 8080

# Localhost only
tinytot --host 127.0.0.1 --port 8080

# As a variant
TINYTOT_DATA_DIR=~/nanotot-bird tinytot --port 11435
```

---

## Using python -m

If the `tinytot` console script isn't in PATH (e.g., before `make install`),
use the module form:

```bash
pipenv run python -m tinytot.server -p "What is pi?"
# → Pi (π) is approximately 3.14159...
```

---

## Shell completion

You can wrap `tinytot -p` in a shell alias for quick interactive use:

```bash
# ~/.zshrc or ~/.bashrc
alias tot='tinytot -p'

tot "What is the speed of light?"
# → The speed of light in a vacuum is approximately 299,792,458 metres per second...
```

---

## Reasoning parity (`tinytot-parity`)

Analyses opencode session exports and compares TinyToT's reasoning/routing
against the models that produced the traces.

```
tinytot-parity [export_dir] {fidelity,cross,routing,all} [--json] [--category-dir DIR]
```

| Check | What it measures |
|---|---|
| `fidelity` | Extraction fidelity of the reasoning trace vs. the original export |
| `cross` | Cross-provider reasoning similarity (jaccard) |
| `routing` | TinyToT routing parity: routed category vs. expected category per export |
| `all` | Run all three checks (default) |

| Flag | Description |
|---|---|
| `export_dir` | Directory of opencode session exports (default: `data/.sources/opencode`) |
| `--json` | Emit raw JSON instead of a text report |
| `--category-dir DIR` | Category dir used for routing parity |

**Examples:**

```bash
tinytot-parity                 # all checks on the default export dir
tinytot-parity routing         # routing parity only
tinytot-parity all --json      # machine-readable output
tinytot-parity fidelity /path/to/exports
```

---

## Trace ingestion (`tinytot-ingest`)

Ingests trace corpora into TinyToT categories.

```
tinytot-ingest {gsm8k,tot-princeton,opentraces,opencode,cs-chains,translate-packs,all}
```

| Source | What it does |
|---|---|
| `gsm8k` | GSM8K math JSONL → `data/knowledge/gsm8k_test.md` |
| `tot-princeton` | Clone/update princeton-nlp/tree-of-thought-llm → game24 + creative_writing chains |
| `opentraces` | Download OpenTraces from Hugging Face → classify into existing categories |
| `opencode` | Ingest `opencode export` sessions → `opencode_augment_*.md` chains |
| `cs-chains` | Generate curated CS reasoning chains (algorithms, data structures, system design) |
| `translate-packs` | Install argostranslate language packs for offline translation |
| `all` | Run every source |

**Examples:**

```bash
tinytot-ingest opencode                       # ingest exported sessions
tinytot-ingest opencode --session <id>        # export then ingest
tinytot-ingest opencode --limit 10            # cap sessions processed
tinytot-ingest all
```

See [Ingesting Corpora](08_ingesting_corpora.md) for details.
