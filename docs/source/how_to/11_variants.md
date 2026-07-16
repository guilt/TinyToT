# How-To: Variants and Self-Replication

TinyToT can clone itself as a **minimal delta** — a tiny directory that layers a
personality and optional domain knowledge on top of the shared base install.
The base package (24K+ passages, 648 code templates, all categories) is never copied.

---

## Quick start

```bash
# Create a bird variant (single 174-byte file)
tinytot-clone ~/nanotot-bird --variant bird

# Run the variant
TINYTOT_DATA_DIR=~/nanotot-bird tinytot -p hello
# → Chirp chirp! I'm TinyToT Bird — your feathered knowledge companion...

# Start the server as the variant
TINYTOT_DATA_DIR=~/nanotot-bird tinytot
```

---

## Built-in variants

| Variant | Greeting |
|---|---|
| `bird` | Chirp chirp! I'm TinyToT Bird — your feathered knowledge companion. Ask me anything about birds, or anything else! |
| `dino` | ROARRR! I'm TinyToT Dino — 65 million years of knowledge (and counting). Ask me about dinosaurs, or anything else! |
| `dog` | Woof! I'm TinyToT Doggo — loyal, fast, and always ready to fetch an answer. What can I sniff out for you? |

---

## Adding domain knowledge to a variant

Pass `--extra-knowledge` to layer `.md` files into the variant's knowledge corpus.
Files with the same stem as base knowledge files replace them; new files extend the corpus.

```bash
# Create a dino variant with extra paleontology knowledge
tinytot-clone ~/nanotot-dino \
  --variant dino \
  --extra-knowledge paleontology.md cretaceous_facts.md

# Files in the delta:
# ~/nanotot-dino/
#   variant.yaml
#   knowledge/
#     paleontology.md
#     cretaceous_facts.md
```

The format for knowledge files is the same as base knowledge — one fact per blank-line-separated paragraph:

```markdown
## Dinosaurs

Dinosaurs were reptiles that dominated land for 165 million years.

Tyrannosaurus rex had binocular vision and arms too short to reach its mouth.

The largest dinosaurs were sauropods — Argentinosaurus may have reached 80 tonnes.
```

---

## How the overlay works

```{mermaid}
flowchart LR
    BASE["Base install\ntinytot/_data/knowledge/\n60+ .md files"]
    DELTA["Delta dir\n~/nanotot-dino/knowledge/\ndinos.md"]
    BASE --> M["Merge by stem\ndelta overrides base"]
    DELTA --> M
    M --> IDX["Knowledge index\n24K+ passages + delta"]
```

At startup, `loadKnowledgePassages` scans the base install knowledge directory,
then overlays any files from the delta. If both have `general.md`, the delta wins.

---

## Creating a custom variant from Python

```python
from tinytot.clone import clone

# Built-in variant
dest = clone("~/nanotot-bird", variant="bird")

# Custom variant with extra knowledge
dest = clone(
    "~/nanotot-science",
    extra_knowledge=["quantum_physics.md", "biochemistry.md"],
    overwrite=True,
)

print(f"Run with: TINYTOT_DATA_DIR={dest} tinytot")
```

---

## Creating your own variant personality

Create a `variant.yaml` manually in any directory:

```yaml
variant: cat
greeting: "Meow. I am TinyToT Neko. I will answer your questions... if I feel like it."
name: TinyToT Neko
emoji: "🐱"
```

Then point `TINYTOT_DATA_DIR` at the directory containing it:

```bash
mkdir ~/nanotot-cat
cp variant.yaml ~/nanotot-cat/
TINYTOT_DATA_DIR=~/nanotot-cat tinytot -p hello
# → Meow. I am TinyToT Neko...
```

---

## Variant sub-spawning

A variant can itself spawn further sub-variants — each sub-variant gets its own
delta directory and runs as an independent instance:

```bash
# From nanotot-bird, create a subspecies
TINYTOT_DATA_DIR=~/nanotot-bird tinytot-clone ~/nanotot-parrot \
  --extra-knowledge parrots.md

TINYTOT_DATA_DIR=~/nanotot-parrot tinytot -p hello
```

---

## Delta directory structure

```
~/nanotot-dino/          ← TINYTOT_DATA_DIR points here
  variant.yaml           ← personality (greeting, name, emoji)
  knowledge/             ← optional domain knowledge overlay
    paleontology.md
```

Everything else (categories, codegen, schema, generate YAML) is served from
the base `pip install tinytot` package. No duplication.
