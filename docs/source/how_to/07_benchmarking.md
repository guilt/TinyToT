# 07 — Benchmarking

TinyToT includes a built-in benchmark suite that measures routing accuracy,
knowledge retrieval precision, and answer quality at scale. All **7 benchmarks**
run automatically as a pre-commit regression guard — a commit is rejected if
any benchmark regresses below its recorded baseline.

## Quick run

```bash
# All benchmarks
make bench

# Individual benchmarks
pipenv run python -m tinytot.benchmark routing
pipenv run python -m tinytot.benchmark retrieval
pipenv run python -m tinytot.benchmark summarize
pipenv run python -m tinytot.benchmark codegen
pipenv run python -m tinytot.benchmark novel-math
pipenv run python -m tinytot.benchmark novel-reasoning
pipenv run python -m tinytot.benchmark novel-routing
```

## What each benchmark measures

### Routing accuracy

Tests **53 canonical prompts** across all dispatch stages, measuring whether
each prompt routes to the correct handler.

```
Current result: 100% (53/53)
Categories: math, programming, aws, tool_calling, financial,
            fs, computer_science, creative_writing, game24
```

### Knowledge retrieval precision

Tests 15 factual questions, measuring whether the top-scored passage from the
five-head retrieval pipeline contains the expected answer token.

```
Current result: 100% (15/15)
```

### Summarization quality

Tests 11 documents spanning 11 domains (climate science, medical trials,
contract law, WWII history, fiction, and more).

```
Current result: 100% (11/11)
```

### Code generation correctness

Tests 50 prompts across 7+ languages verifying that template selection and
language detection produce syntactically correct, runnable code.

```
Current result: 98% (49/50)
```

### Novel math (anti-cheat)

Tests 25 arithmetic and word problems with **randomly generated numbers**
(seed-controlled). Because the numbers change each run, this benchmark cannot
be gamed by memorising answers.

```
Current result: 100% (25/25)
Change the seed to verify no caching: pipenv run python -m tinytot.benchmark novel-math --seed 99
```

### Novel reasoning (anti-cheat)

Tests 18 **held-out paraphrased prompts** that do not appear verbatim in any
knowledge file or chain. Tests genuine generalisation: propositional logic,
coreference, contradiction, structured data, and domain knowledge.

```
Current result: 100% (18/18)
```

### Novel routing (anti-cheat)

Tests 22 **novel phrasings** of known intents to probe whether the router
generalises beyond training strings.

```
Current result: 86% (19/22)
Remaining misses are at ambiguous category boundaries.
```

## Current benchmark summary

| Benchmark | Cases | Score | Pass rate |
|---|---|---|---|
| Routing accuracy | 53 | 53/53 | 100% |
| Knowledge retrieval | 15 | 15/15 | 100% |
| Summarization | 11 | 11/11 | 100% |
| Code generation | 50 | 49/50 | 98% |
| Novel math | 25 | 25/25 | 100% |
| Novel reasoning | 18 | 18/18 | 100% |
| Novel routing | 22 | 19/22 | 86% |

## Pre-commit regression guard

The pre-commit hook runs all 7 benchmarks before every commit. If any benchmark
regresses below baseline, the commit is blocked:

```bash
$ git commit -m "feat: update routing"

benchmark regression guard...................Passed

==========================================================
  Benchmark Regression Report
==========================================================
  PASSED   codegen               49  (baseline 49) [=]
  PASSED   novel_math            25  (baseline 25) [=]
  PASSED   novel_reasoning       18  (baseline 18) [=]
  PASSED   novel_routing         19  (baseline 19) [=]
  PASSED   retrieval             15  (baseline 15) [=]
  PASSED   routing               53  (baseline 53) [=]
  PASSED   summarization         11  (baseline 11) [=]
==========================================================

  All benchmarks at or above baseline.
```

If a benchmark regresses, the commit is blocked with a diff showing which cases
dropped. Fix the regression, re-stage, and commit again. To intentionally accept
a change: `pipenv run python -m tinytot.tests.check_benchmarks --update-baseline`.

The baseline is stored in `tinytot/_data/benchmarks_baseline.json`. It auto-advances when
scores improve — ratchet-only.

## Interpreting results

```
================================================================
  Routing Accuracy Benchmark
================================================================
  total: 53
  correct: 53
  accuracy_pct: 100.0
  avg_query_ms: 0.3
  misrouted: []
```

`avg_query_ms` is per-prompt classification time. `misrouted` entries print the
prompt, expected category, and actual category — making regressions trivial to debug.

## Running the breadth benchmark

```bash
pipenv run python3 << 'EOF'
from tinytot.inference import generateReasoningResponse
from tinytot.retrieval import buildKnowledgeIndex
from tinytot.content import loadKnowledgePassages
buildKnowledgeIndex.cache_clear(); loadKnowledgePassages.cache_clear()

cases = [
    ("What is the Heisenberg uncertainty principle?", "momentum"),
    ("What is normal blood pressure?", "120"),
    ("What is mens rea?", "intention"),
    ("What is CAPM?", "beta"),
    ("What is a race condition?", "thread"),
    ("How many r's in strawberry?", "3"),
    ("If 3x + 7 = 22, x?", "5"),
    ("A implies B, B implies C, A is true. Is C true?", "yes"),
    ("Alice=85, Bob=92. Who scored higher?", "bob"),
]
hits = sum(1 for q, exp in cases if exp.lower() in generateReasoningResponse(q).lower())
print(f"Score: {hits}/{len(cases)} = {hits/len(cases)*100:.0f}%")
buildKnowledgeIndex.cache_clear(); loadKnowledgePassages.cache_clear()
EOF
```

## Adding new benchmark cases

Edit `tinytot/benchmark.py` — add entries to the relevant list:

```python
# Routing cases
_ROUTING_CASES = [
    ...
    ("Rewrite this in a more Pythonic way: x = x + 1", "programming"),
]

# Retrieval cases
_RETRIEVAL_CASES = [
    ...
    ("What is the Heisenberg uncertainty principle?", "momentum"),
]

# Novel reasoning cases (paraphrased, not in training data)
_NOVEL_REASONING_CASES = [
    ...
    ("Maria told Julia she had won. Who won?", ["Maria", "maria"]),
]

# Novel routing cases (novel phrasings of known intents)
_NOVEL_ROUTING_CASES = [
    ...
    ("Help me brainstorm app ideas", "general_knowledge"),
]
```

After adding cases, run `make bench` to verify they pass. The pre-commit hook
enforces them on all future commits.

## Next Steps

- **[Knowledge Base](01_knowledge_base.md)** — improve retrieval precision
- **[Reasoning Chains](03_reasoning_chains.md)** — improve routing accuracy
- **[Ingesting Corpora](08_ingesting_corpora.md)** — add more knowledge at scale
