# 03 — Reasoning Chains

Reasoning chains define step-by-step approaches for domains where the answer requires
a process, not just a lookup. When no direct knowledge match is found, TinyToT routes
the prompt to the best-matching chain and returns a structured reasoning trace.

## What a reasoning chain looks like

```markdown
---
category: math
---

# Math Reasoning Chains

## Chain 1: Arithmetic
<!-- Handles: calculate, add, multiply, arithmetic -->
Thought 1: Identify the arithmetic operation: addition, subtraction, multiplication.
Thought 2: Apply the operation step by step to evaluate the expression.
Thought 3: Verify the result by substituting back.
```

The YAML frontmatter declares the category name used for routing. The `## Chain N:`
header names the chain. Thoughts are the steps shown in the reasoning trace.

## Adding a new domain

```bash
cat > tinytot/_data/categories/security.md << 'EOF'
---
category: security
keywords: vulnerability, exploit, injection, xss, csrf, authentication, encryption
---

# Security Reasoning Chains

## Chain 1: Vulnerability Assessment
<!-- Handles: vulnerability, security issue, attack, exploit, bug -->
Thought 1: Identify the attack surface: input validation, authentication, authorisation.
Thought 2: Classify the vulnerability type: injection, broken auth, XSS, IDOR, etc.
Thought 3: Assess impact and exploitability using CVSS scoring criteria.
Thought 4: Recommend remediation: input sanitisation, parameterised queries, CSP headers.

## Chain 2: Secure Code Review
<!-- Handles: code review, security review, audit, check code -->
Thought 1: Scan for OWASP Top 10: injection flaws, XSS, insecure deserialisation.
Thought 2: Check authentication and session management patterns.
Thought 3: Verify input validation at all trust boundaries.
Thought 4: Confirm secrets are not hardcoded and dependencies are patched.
EOF
```

Restart the server — the category is discovered and indexed automatically.

## How routing works

TinyToT builds a TF-IDF vector for each chain (title + all thoughts combined).
When a prompt arrives, it computes cosine similarity against all chain vectors
and picks the highest-scoring category.

**The rule:** the chain that shares the most vocabulary with the prompt wins.
If routing goes wrong, the fix is always to enrich the correct chain's thoughts
with the vocabulary that appears in real user queries.

```bash
# Check current routing for a prompt
pipenv run python3 -c "
from tinytot.retrieval import buildChainIndex, queryVector, cosineSim, categorizePrompt
from tinytot.content import getCategories, loadReasoningChains
getCategories.cache_clear(); loadReasoningChains.cache_clear()
buildChainIndex.cache_clear()
print('Routes to:', categorizePrompt('explain SQL injection'))
buildChainIndex.cache_clear()
"
```

## Knowledge grounding

When the knowledge base has a relevant passage (score ≥ 0.20), the reasoning trace
is **grounded** — the passage becomes the `Conclusion:` of the trace. This combines
the structured reasoning approach with accurate factual anchoring.

```
Step 1: Identify the type of security vulnerability.
Step 2: Assess the injection surface and exploitability.
Step 3: Recommend parameterised queries or prepared statements.

Conclusion: SQL injection occurs when user input is included in a SQL query
            without sanitisation. Prevent with parameterised queries or
            prepared statements.
```

## Chain vocabulary tips

- **Use the words users actually say.** If users ask "how do I fix a segfault",
  your debugging chain should contain "segfault", "crash", "debug" — not just
  "memory access violation".
- **Thoughts don't need to be complete sentences.** Dense keyword coverage matters
  more for routing than prose quality.
- **More chains = better routing precision.** A category with 10 chains can
  differentiate between "calculate derivative" and "solve equation". A category
  with 1 chain treats them the same.

## Real-world example

The current `tinytot/_data/categories/math.md` routes correctly because:

```markdown
## Chain 1: Arithmetic
<!-- Handles: calculate, multiply, addition, arithmetic, expression -->
Thought 1: Identify the arithmetic operation: addition, subtraction, multiplication.
Thought 2: Apply order of operations: multiply and divide before add and subtract.
Thought 3: Calculate 15 times 23 equals 345, then add 7 equals 352.
```

The phrase "15 times 23" in the thought gives TF-IDF signal for "times" that beats
the `fs` category which also uses the word "times" in "File Synchronization times".

## Next Steps

- **[Tool Calling](04_tool_calling.md)** — when reasoning needs external data
- **[Knowledge Base](01_knowledge_base.md)** — facts that ground the chains
