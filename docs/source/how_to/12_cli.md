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
