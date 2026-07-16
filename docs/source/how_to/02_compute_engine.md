# 02 — Compute Engine

TinyToT solves a wide class of problems through direct computation rather than
retrieval. This is how it handles out-of-distribution arithmetic that neural language
models get wrong because they *predict* rather than *compute*.

## What the compute engine handles

| Category | Examples |
|---|---|
| **Arithmetic** | `347 * 18`, `sqrt(256)`, `5!`, `2 to the power of 10` |
| **Word arithmetic** | `seventeen times thirteen`, `twice as many` |
| **Algebra** | `If 3x + 7 = 22, x = ?`, `y = 2x + 3, x = 4` |
| **Geometry** | Rectangle perimeter/area, circle area, sphere volume, hypotenuse |
| **Percentages** | `15% of 840`, `30% profit on $50`, `Y increased by X%` |
| **Chained percentages** | `$120 discounted 25% then taxed 8%` → `$97.20` |
| **Fraction of total** | `12 slices, Alice 3, Bob 4, Carol the rest. Fraction Carol?` → `5/12` |
| **Unit conversion** | `32°F to Celsius`, `100 miles to km`, `3 days to hours` |
| **Letter counting** | `How many r's in strawberry?`, `Letters in banana` |
| **Work rate** | `3 workers in 6h → 9 workers = ?` |
| **Multi-leg distance** | `60km/h 2h then 80km/h 1h` → `220` |
| **Multi-step word problems** | `Apples $0.50 each, oranges $0.75 each. 4 apples + 3 oranges?` → `$4.25` |
| **Age arithmetic** | `Tom is 5 older than Sue. Sue is 12. Tom in 3 years?` |
| **Structured data** | `Alice=85, Bob=92, Carol=78. Who scored highest?` → `Bob (92)` |
| **Propositional logic chains** | `A implies B, B implies C, A is true. Is C true?` → `Yes` |
| **Coreference** | `Alice told Bob she was leaving. Who was leaving?` → `Alice` |
| **Contradiction detection** | `'All birds fly' vs 'Penguins are birds that cannot fly'` → `Contradiction` |
| **Logic deduction** | Modus ponens, negation, transitive relations (taller/older/…) |

## Safety

The engine uses Python's `ast` module to parse expressions. `eval()` and `exec()`
are **never called**. The AST is walked with a strict whitelist: only `Constant`,
`BinOp`, `UnaryOp`, and whitelisted `Call` nodes (`sqrt`, `factorial`, `abs`)
are permitted. Any other node raises an error and returns `None`.

## Examples

```bash
# Basic arithmetic
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"What is 347 * 18?","stream":false}'
# → "6246"

# Algebra
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"If 5x - 3 = 22, what is x?","stream":false}'
# → "5"

# Letter counting (notorious LLM failure mode)
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"How many r'\''s in strawberry?","stream":false}'
# → "3"

# Unit conversion
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"Convert 100 miles to km","stream":false}'
# → "160.9344 km"

# Chained percentages
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"A product costs $120 discounted 25% then taxed 8%. Final price?","stream":false}'
# → "$97.20 (-25% discount: $120 × 0.75 = $90; +8% tax: $90 × 1.08 = $97.20)"

# Fraction of total
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"12 slices. Alice ate 3, Bob ate 4, Carol ate the rest. What fraction did Carol eat?","stream":false}'
# → "Carol ate 5/12 of the pizza."

# Multi-step shopping
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"Apples $0.50 each, oranges $0.75 each. I buy 4 apples and 3 oranges. Total?","stream":false}'
# → "$4.25 (4 × $0.5 = $2; 3 × $0.75 = $2.25)"

# Structured data
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"Given: Alice=85, Bob=92, Carol=78. Who has the highest score?","stream":false}'
# → "Bob (92)."

# Propositional logic chain
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"A implies B and B implies C. A is true. What can we conclude?","stream":false}'
# → "By modus ponens: A → B → C. Since A is true, C is also true."

# Coreference
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"Alice told Bob that she was leaving. Who was leaving?","stream":false}'
# → "Alice was leaving."

# Contradiction
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"Does '\''All birds can fly'\'' contradict '\''Penguins are birds that cannot fly'\''?","stream":false}'
# → "Yes, these statements contradict each other..."

# Classic logic deduction
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"No reptiles are warm-blooded. A snake is a reptile. Is a snake warm-blooded?","stream":false}'
# → "No. A snake is not warm-blooded because no reptiles are warm-blooded."

# Multi-step word problem
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"Alice has 8 apples. Bob has half as many. Carol has 3 more than Bob. Total?","stream":false}'
# → "19"
```

## Why this matters vs. LLMs

Letter counting is a canonical example. "How many r's in strawberry?" has appeared in
billions of training documents with inconsistent or missing answers. A neural model
predicts a likely token — often wrong. TinyToT counts characters:
`"strawberry".count('r') == 3`. Exact, always.

The same principle applies to propositional logic chains, coreference, contradiction
detection, and structured data comparisons. These are **computation problems**, not
**retrieval problems**. Treating them as retrieval wastes parameters on memorising
answers that can be derived.

## Testing compute detection

```bash
pipenv run python3 << 'EOF'
from tinytot.compute import detectComputePrompt, solveCompute

prompts = [
    "What is 17 * 13?",
    "If 3x + 7 = 22, x?",
    "Area of circle radius 5",
    "How many e's in elephant?",
    "All mammals warm-blooded. Dolphins mammals. Warm-blooded?",
    "A implies B, B implies C, A is true. Is C true?",
    "Alice=85, Bob=92. Who scored higher?",
    "Price $100, up 20%, down 10%. Final?",
    "12 slices, Alice 3, Bob 4, Carol the rest. Carol's fraction?",
]
for p in prompts:
    det = detectComputePrompt(p)
    result = solveCompute(p) if det else None
    print(f"{'COMPUTE' if det else 'retrieval':10s}  {result or '—':25s}  {p}")
EOF
```

## Next Steps

- **[Reasoning Chains](03_reasoning_chains.md)** — for multi-step domain reasoning
- **[Knowledge Base](01_knowledge_base.md)** — for facts that don't need computation
