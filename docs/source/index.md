# TinyToT

**Tree of Thoughts Inference Server** — 100% benchmark accuracy on 7 suites,
zero parameters, no GPU, runs on a laptop CPU.

---

## The thesis

Large language models are solving two fundamentally different problems with the
same mechanism — gradient descent — and charging you for both.

**Problem 1: Fact storage.** FFN layers in transformers act as key-value memories
(Geva et al., 2021). A 7B model uses ~4.2B parameters (60%) to store facts. You
can surgically edit individual neurons to change specific facts (Meng et al., 2022).
This is an expensive, lossy, hallucination-prone database stored in floating point.

**Problem 2: Composition.** Combining retrieved facts into coherent answers.
This requires attention, context, and generation — maybe 30–50M parameters based
on LoRA, Phi-1, and distillation research.

TinyToT replaces Problem 1 with text files. Zero parameters for storage.
What remains is a routing and composition problem that needs far less than
anyone has been building.

---

## Benchmark results

| Benchmark | Score |
|---|---|
| Routing accuracy | **100% (53/53)** |
| Knowledge retrieval | **100% (15/15)** |
| Summarization (11 domains) | **100% (11/11)** |
| Code generation (7+ languages) | **98% (49/50)** |
| Novel math (random seeds) | **100% (25/25)** |
| Novel reasoning (held-out) | **100% (18/18)** |
| Novel routing (unseen phrasings) | **100% (22/22)** |

Run all benchmarks: `make bench`

---

## Documentation

```{toctree}
:maxdepth: 1
:caption: Get started

getting_started
```

```{toctree}
:maxdepth: 1
:caption: Guides

guides/concepts
guides/architecture
```

```{toctree}
:maxdepth: 1
:caption: How-To

how_to/index
```

```{toctree}
:maxdepth: 1
:caption: Reference

api/README
```

---

## Architecture

```{mermaid}
flowchart TD
    P([Prompt]) --> N[0a Normalise]
    N --> R[0b Multi-turn refine]
    R --> S[0c Project scaffold]
    S --> U[0d Use-case handler]
    U --> J[1 JSON scoring]
    J --> SU[2 Summarize]
    SU --> C[3 Compute]
    C --> SO[4 Social / greeting]
    SO --> A[5 Agent tools]
    A --> L[6 Live-data guard]
    L --> K[7 Knowledge retrieval]
    K --> CG[8 Code generation]
    CG --> T[9 Tree of Thoughts]

    SO -- variant greeting --> V([Variant response])
    C -- exact result --> ANS([Answer])
    K -- passage found --> ANS
    CG -- template hit --> ANS
    T --> ANS
```

See [Architecture Guide](guides/architecture) for the full explanation.

---

## Variants and self-replication

TinyToT can clone itself as a lightweight variant — just a `variant.yaml` delta
(174 bytes) that overrides the greeting and adds domain knowledge on top of the
shared base install.

```bash
tinytot-clone ~/nanotot-bird --variant bird
TINYTOT_DATA_DIR=~/nanotot-bird tinytot -p hello
# → Chirp chirp! I'm TinyToT Bird — your feathered knowledge companion...
```

Built-in variants: `bird`, `dino`, `dog`. See [How-To: Variants](how_to/11_variants).
