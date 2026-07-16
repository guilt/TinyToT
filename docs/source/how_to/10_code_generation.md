# 10 — Code Generation

TinyToT generates runnable code for 648 algorithm templates across 13 languages
(Python, JavaScript, TypeScript, Go, Rust, Java, Ruby, Swift, C++, C#, Kotlin, SQL, Bash)
with zero neural weights. It also generates multi-file project scaffolds.
Everything lives in plain files you can edit.

---

## Two modes

### Mode 1: Single-file template
```
query: "Write a Python function to reverse a string"
  │
  ├─ tinytot/_data/codegen/patterns.yaml  →  matches key: "reverse_string"
  ├─ detectLanguage(query)        →  "python"
  ├─ tinytot/_data/codegen/templates/reverse_string.md  →  ## python section
  └─ return fenced code block
```

### Mode 2: Multi-file project scaffold
```
query: "Build a Flask REST API with a users endpoint"
  │
  ├─ tinytot/_data/codegen/projects.yaml  →  matches blueprint: flask_api
  └─ return Markdown with app.py + tests/ + requirements.txt + README.md
```

---

## Data files

| File | Purpose |
|---|---|
| `tinytot/_data/codegen/patterns.yaml` | regex → template key mappings (648 patterns) |
| `tinytot/_data/codegen/config.yaml` | language detection, fence labels, request patterns |
| `tinytot/_data/codegen/templates/<key>.md` | one file per algorithm, one section per language |
| `tinytot/_data/codegen/decompositions.yaml` | compositional problem breakdowns |
| `tinytot/_data/codegen/projects.yaml` | multi-file project blueprints |

---

## Available project blueprints

| Blueprint key | Generates |
|---|---|
| `flask_api` | app.py (CRUD) + tests + requirements.txt + README |
| `fastapi_api` | main.py + Pydantic models + tests + README |
| `python_cli` | cli.py + argparse subcommands + tests + README |
| `data_pipeline` | pipeline.py (ETL) + tests + README |
| `python_package` | src layout + pyproject.toml + tests + README |

Trigger with natural language: "Build a Flask REST API", "Create a Python CLI tool", etc.

---

## Multi-turn refinement

After receiving code, the following follow-up prompts transform it:

| Intent | Trigger example |
|---|---|
| `make_async` | "make it async" |
| `add_types` | "add type hints" |
| `add_error_handling` | "add error handling" |
| `add_logging` | "add logging" |
| `add_docstring` | "add docstrings" |
| `simplify` | "simplify", "refactor" |
| `add_tests` | "add unit tests" |
| `explain` | "explain this code" |

---



### 1. Create the template file

```bash
cat > tinytot/_data/codegen/templates/longest_palindrome.md << 'EOF'
# Longest Palindromic Substring

## python
```python
def longest_palindrome(s: str) -> str:
    """Return the longest palindromic substring using expand-around-center."""
    if not s:
        return ""
    start = end = 0
    for i in range(len(s)):
        for l, r in [(i, i), (i, i + 1)]:   # odd and even length
            while l >= 0 and r < len(s) and s[l] == s[r]:
                l -= 1
                r += 1
            if r - l - 2 > end - start:
                start, end = l + 1, r - 1
    return s[start:end + 1]

# Example
print(longest_palindrome("babad"))  # "bab" or "aba"
print(longest_palindrome("cbbd"))   # "bb"
```

## javascript
```javascript
function longestPalindrome(s) {
    let start = 0, maxLen = 1;
    function expand(l, r) {
        while (l >= 0 && r < s.length && s[l] === s[r]) { l--; r++; }
        if (r - l - 1 > maxLen) { maxLen = r - l - 1; start = l + 1; }
    }
    for (let i = 0; i < s.length; i++) { expand(i, i); expand(i, i+1); }
    return s.slice(start, start + maxLen);
}
```
EOF
```

Rules:
- One `## <language>` section per language (lowercase).
- Fenced block label: use `cpp` for C++, `csharp` for C#.
- **No demo `fn main()` or `int main()` inside the function body** — the
  execution test harness appends its own entry point.
- Include a Python example call in a comment at the bottom.

### 2. Add a pattern

```bash
# Append to tinytot/_data/codegen/patterns.yaml
cat >> tinytot/_data/codegen/patterns.yaml << 'EOF'

  - pattern: '\blongest\s+palindrom(?:e|ic)\b|\bpalindromic\s+substring\b'
    key: longest_palindrome
    note: "Longest Palindromic Substring"
EOF
```

Pattern rules:
- Python `re` syntax, `IGNORECASE` applied automatically.
- More specific patterns must come before broad ones in the file.
- Test your pattern before committing: `pipenv run python3 -c "from tinytot.codegen import _matchPattern, _loadPatterns; _loadPatterns.cache_clear(); print(_matchPattern('find the longest palindromic substring'))"`

### 3. Test it

```bash
pipenv run python3 -c "
from tinytot.codegen import generateCode, _loadPatterns, _loadConfig
_loadPatterns.cache_clear(); _loadConfig.cache_clear()
r = generateCode('Find the longest palindromic substring in Python')
print(r)
"
```

### 4. Run the benchmark

```bash
pipenv run python3 -m tinytot.benchmark codegen
```

All 49 existing cases should still pass. If your new pattern is too broad
and breaks an existing case, tighten it.

---

## Adding a new language to an existing template

Open the template file and add a `## <language>` section:

```bash
# Example: add Go to longest_palindrome.md
cat >> tinytot/_data/codegen/templates/longest_palindrome.md << 'EOF'

## go
```go
func longestPalindrome(s string) string {
    start, maxLen := 0, 1
    expand := func(l, r int) {
        for l >= 0 && r < len(s) && s[l] == s[r] { l--; r++ }
        if r-l-1 > maxLen { maxLen = r - l - 1; start = l + 1 }
    }
    for i := range s { expand(i, i); expand(i, i+1) }
    return s[start : start+maxLen]
}
```
EOF
```

No restart needed — templates are read on every `generateCode()` call.

---

## Supported languages and fence labels

| Language | Section header | Fence label |
|---|---|---|
| Python | `## python` | `python` |
| JavaScript | `## javascript` | `javascript` |
| TypeScript | `## typescript` | `typescript` |
| Java | `## java` | `java` |
| Go | `## go` | `go` |
| Rust | `## rust` | `rust` |
| C++ | `## c++` | `cpp` |
| C# | `## c#` | `csharp` |
| Ruby | `## ruby` | `ruby` |
| Kotlin | `## kotlin` | `kotlin` |
| Swift | `## swift` | `swift` |
| SQL | `## sql` | `sql` |
| Bash | `## bash` | `bash` |

Language detection, fence labels, and request-detection patterns are all in
`tinytot/_data/codegen/config.yaml` — no Python changes needed to add a new language.

---

## Compositional problems

Some problems decompose into sub-problems. Register them in
`tinytot/_data/codegen/decompositions.yaml`:

```yaml
  median:
    description: "median of a list"
    template: median
    composes:
      - template: sort_list
        role: "sort the input"
      - template: median
        role: "pick middle element(s)"
    patterns:
      - '\bmedian\b'
```

When a compositional decomposition exists, `generateCode()` prepends a comment
block explaining the sub-problems before the solution code:

```python
# Composition: median of a list
# Built from: sort_list + median
# Steps:
#   1. sort the input
#   2. pick middle element(s)

def median(nums):
    ...
```

---

## Grug process: one-line checklist

```
1. Create tinytot/_data/codegen/templates/<key>.md  (## python section required)
2. Add pattern to tinytot/_data/codegen/patterns.yaml
3. Run: pipenv run python3 -m tinytot.benchmark codegen
4. All 49 existing cases pass? Commit.
```

That's it. No Python, no restarts, no training.

---

## Next Steps

- **[Ingesting Corpora](08_ingesting_corpora.md)** — bulk-ingest from mirrors or datasets
- **[Benchmarking](07_benchmarking.md)** — `make bench` runs all 5 benchmarks
- **[Extending TinyToT](09_extending.md)** — new response modes, new compute solvers
