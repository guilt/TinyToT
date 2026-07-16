# 09 — Extending TinyToT

TinyToT is designed for extension. The system is data-driven:
**most additions require only YAML or Markdown edits, no Python changes.**

## Quickref: what needs code vs. what doesn't

| To add... | Edit | Code? |
|---|---|---|
| New factual knowledge | `tinytot/_data/knowledge/<domain>.md` | No |
| New reasoning category | `tinytot/_data/categories/<domain>.md` | No |
| New code template | `tinytot/_data/codegen/templates/<key>.md` + `patterns.yaml` | No |
| New project blueprint | `tinytot/_data/codegen/projects.yaml` | No |
| New how-to guide | `tinytot/_data/generate/howto_scripts.yaml` | No |
| New static code check | `tinytot/_data/generate/static_checks.yaml` | No |
| New haiku topic | `tinytot/_data/generate/creative/haiku_topics.yaml` | No |
| New story template | `tinytot/_data/generate/creative/story_templates.yaml` | No |
| New formality substitution | `tinytot/_data/generate/rewrite_subs.yaml` | No |
| New entity extractor | `tinytot/_data/generate/extractors.yaml` | No |
| New comparative adjective | `tinytot/_data/generate/comparatives.yaml` | No |
| New use-case handler | `tinytot/_data/generate/use_cases.yaml` + handler fn | Minimal |
| New compute solver | `tinytot/compute.py` | Yes |

---

## Adding a new knowledge domain

```bash
cat > tinytot/_data/knowledge/my_domain.md << 'EOF'
## My Domain

The first important fact about my domain, stated clearly and concisely.

## Related Topic

A second paragraph covering a related subtopic.
EOF
```

Restart the server. Done. No code changes.

---

## Adding a new use-case handler (tinytot/_data/generate/)

The `generate.py` dispatch layer reads all patterns and content from YAML.

### To add a new how-to guide:

```yaml
# tinytot/_data/generate/howto_scripts.yaml
  - trigger: 'read\s+parquet\s+file|load\s+parquet'
    title: Read a Parquet file in Python
    steps:
      - "Install: `pip install pandas pyarrow`"
      - "Read: `df = pd.read_parquet('data.parquet')`"
      - "Inspect: `print(df.head())`"
```

### To add a new static code check:

```yaml
# tinytot/_data/generate/static_checks.yaml
  - pattern: '\bprint\s*\('
    message: "debug `print()` — use `logging` for production code"
```

### To add a new use-case handler (requires a Python handler function):

1. Add a pattern entry to `tinytot/_data/generate/use_cases.yaml`
2. Add a handler function `_handle_mycase(prompt: str) -> str` in `tinytot/generate.py`
3. Register it in `_HANDLERS` dict at the bottom of `generate.py`

---

## Adding a new compute solver

The compute engine is a chain of solvers tried in priority order.

**1. Write the solver in `tinytot/compute.py`:**

```python
def _solveMyDomain(prompt: str) -> Optional[str]:
    """Detect and solve my-domain queries. Returns answer or None."""
    m = re.search(r"my pattern (\d+)", prompt, re.IGNORECASE)
    if not m:
        return None
    value = int(m.group(1))
    return str(my_computation(value))
```

**2. Add detection triggers to `_COMPUTE_TRIGGER_PATTERNS`:**

```python
re.compile(r"\bmy domain keyword\b", re.IGNORECASE),
```

**3. Add to the dispatcher in `solveCompute`:**

```python
answer = _solveMyDomain(prompt)
if answer is not None:
    return answer
```

---

## Adding a new reasoning chain category

```bash
cat > tinytot/_data/categories/my_category.md << 'EOF'
---
category: my_category
keywords: keyword1, keyword2, keyword3
---

# My Category

## Chain 1: My Approach
<!-- Handles: specific, triggers -->
Thought 1: First reasoning step.
Thought 2: Second step.
Thought 3: Conclusion.
Conclusion: The answer is X because Y.
EOF
```

Restart. The category is auto-discovered and added to the routing index.
The `Conclusion:` field is returned directly — chains without it produce the full ToT trace.

---

## Adding a new code template

See [How-To: Code Generation](10_code_generation.md) for the full walkthrough.

---

## Adding a new project blueprint

```yaml
# tinytot/_data/codegen/projects.yaml
  my_project:
    description: "My project scaffold"
    patterns:
      - '\bbuild\s+a\s+my\s+project\b'
    files:
      - path: "main.py"
        content: |
          # Your starter code here
        note: "Entry point"
      - path: "README.md"
        content: |
          # My Project
        note: "Documentation"
```

No code changes needed — `generateProject()` loads blueprints from this file.

---

## Adding a multi-turn refinement intent

Multi-turn code refinement (making prior code async, adding types, etc.) is handled
by `tinytot/refine.py`. To add a new transformation intent:

1. Add a pattern to `_REFINEMENT_PATTERNS` in `refine.py`
2. Add a transformation function `_my_transform(code: str) -> str`
3. Register it in `_TRANSFORMATIONS` dict

---

## Running tests after changes

```bash
pipenv run pytest tinytot/tests -q               # all 335+ tests
pipenv run python -m tinytot.tests.check_benchmarks  # regression guard (7 benchmarks)
pipenv run ruff check tinytot                    # lint
pipenv run ruff format tinytot                   # format
```

Coverage must stay above 80% for core modules. The pre-commit hook runs all of the
above automatically and rejects commits that drop benchmarks below baseline.

---

## Next Steps

- **[Core Concepts](../guides/concepts.md)** — understand the architecture
- **[Benchmarking](07_benchmarking.md)** — measure the impact of your changes

## Adding a new compute solver

The compute engine is a chain of solvers tried in priority order. To add a new one:

**1. Write the solver function in `tinytot/compute.py`:**

```python
def _solveMyDomain(prompt: str) -> Optional[str]:
    """Detect and solve my-domain queries. Returns answer or None."""
    m = re.search(r"my pattern (\d+)", prompt, re.IGNORECASE)
    if not m:
        return None
    value = int(m.group(1))
    return str(my_computation(value))
```

**2. Add detection triggers to `_COMPUTE_TRIGGER_PATTERNS`:**

```python
_COMPUTE_TRIGGER_PATTERNS = [
    ...
    re.compile(r"\bmy domain keyword\b", re.IGNORECASE),
]
```

**3. Add to the dispatcher in `solveCompute`:**

```python
def solveCompute(prompt: str) -> Optional[str]:
    ...
    # Add after existing solvers, before arithmetic
    answer = _solveMyDomain(prompt)
    if answer is not None:
        return answer
    ...
```

**4. Test it:**

```bash
pipenv run python3 -c "
from tinytot.compute import detectComputePrompt, solveCompute
print(detectComputePrompt('my query'))
print(solveCompute('my query'))
"
```

## Adding a new response mode

Response modes are patterns matched before retrieval. To add one:

**1. Add patterns to `tinytot/inference.py`:**

```python
_MY_MODE_PATTERNS = [
    re.compile(r"\bmy trigger phrase\b", re.IGNORECASE),
]
```

**2. Add detection in `detectResponseMode`:**

```python
def detectResponseMode(prompt: str) -> ResponseMode:
    for pattern in _JSON_SCORE_PATTERNS:
        if pattern.search(prompt): return "json_scoring"
    # Add your check (after JSON, before direct/reasoning_trace)
    for pattern in _MY_MODE_PATTERNS:
        if pattern.search(prompt): return "my_mode"
    ...
```

**3. Add a generator function:**

```python
def generateMyModeResponse(
    prompt: str,
    knowledgeDir: Path = KNOWLEDGE_DIR,
) -> str:
    """Handle my-mode queries."""
    # Your logic here
    return result
```

**4. Dispatch in `generateReasoningResponse`:**

```python
def generateReasoningResponse(prompt, categoryDir=CATEGORY_DIR, knowledgeDir=KNOWLEDGE_DIR):
    mode = detectResponseMode(prompt)
    if mode == "json_scoring":
        return generateJsonScoringResponse(prompt, knowledgeDir)
    if mode == "my_mode":
        return generateMyModeResponse(prompt, knowledgeDir)
    ...
```

## Adding a new knowledge domain

```bash
cat > tinytot/_data/knowledge/my_domain.md << 'EOF'
# My Domain

## Key concept one

The first important fact about my domain, stated clearly and concisely.

## Key concept two

The second important fact, leading with the answer so it can be returned directly.
EOF
```

Restart the server. Done. No code changes needed.

## Adding a new reasoning chain category

```bash
cat > tinytot/_data/categories/my_category.md << 'EOF'
---
category: my_category
keywords: keyword1, keyword2, keyword3
---

# My Category Reasoning Chains

## Chain 1: My Approach
<!-- Handles: specific, triggers -->
Thought 1: First step of the reasoning process.
Thought 2: Second step with the vocabulary users actually use.
Thought 3: Conclude with a verifiable result.
EOF
```

Restart. The category is auto-discovered and added to the routing index.

## Adding a new journal format

TinyToT currently auto-detects Hermes journals. To add support for another format:

**1. Add a detection function in `tinytot/content.py`:**

```python
_MY_FORMAT_RE = re.compile(r"my provenance pattern")

def _isMyFormat(lines: list[str]) -> bool:
    return any(_MY_FORMAT_RE.match(line.rstrip()) for line in lines)

def loadMyFormat(path: Path) -> list[KnowledgePassage]:
    """Parse my journal format into knowledge passages."""
    passages = []
    # your parsing logic
    return passages
```

**2. Register in `loadKnowledgePassages`:**

```python
if _isHermesJournal(lines):
    passages.extend(loadHermesJournal(md_file))
elif _isMyFormat(lines):
    passages.extend(loadMyFormat(md_file))
else:
    # plain knowledge format
    ...
```

## Running tests after changes

```bash
pipenv run pytest tinytot/tests -q          # all tests
pipenv run pytest tinytot/tests -q -k "compute"  # only compute tests
pipenv run ruff check tinytot               # lint
pipenv run ruff format tinytot              # format
```

Coverage must stay above 80% for core modules (content, inference, retrieval,
server, tools). New compute and ingest functions are excluded from the gate.

## Next Steps

- **[Core Concepts](../guides/concepts.md)** — understand the architecture before extending
- **[Benchmarking](07_benchmarking.md)** — measure the impact of your changes
