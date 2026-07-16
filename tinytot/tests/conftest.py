"""
Shared pytest fixtures — a self-contained in-memory category directory
so tests never touch the real data/ folder.
"""

from pathlib import Path

import pytest

MATH_MD = """\
---
category: math
keywords: calculate, equation, solve, multiply, add, subtract, divide, arithmetic, algebra, variable
---

# Math Reasoning Chains

## Chain 1: Arithmetic
<!-- Handles: calculate, add, multiply, arithmetic, expression -->
Thought 1: Identify the arithmetic operation: addition, subtraction, multiplication, or division.
Thought 2: Apply the calculate operation step by step to evaluate the expression.
Thought 3: Verify the result by substituting back into the equation.

## Chain 2: Algebra
<!-- Handles: solve, equation, variable, isolate, algebra -->
Thought 1: Isolate the variable on one side of the equation.
Thought 2: Perform inverse operations to solve and calculate the value.
Thought 3: Substitute back to verify the equation holds.
"""

TOOL_MD = """\
---
category: tool_calling
keywords: search, lookup, fetch, retrieve, news, weather, wikipedia, browse, web, internet, latest, real-time
---

# Tool Calling Chains

## Chain 1: Web Search
<!-- Handles: search, browse, news, latest, web, internet, ddg -->
Thought 1: User needs live or current web content not available offline.
Thought 2: Formulate a precise search query using topic keywords.
Thought 3: Invoke the search tool and synthesise retrieved snippets.

## Chain 2: Real-Time Data Fetch
<!-- Handles: weather, forecast, temperature, stock, price, live, real-time, today -->
Thought 1: Request requires live time-sensitive data unavailable in static knowledge.
Thought 2: Identify the appropriate real-time API tool for weather or finance.
Thought 3: Call the tool with the relevant location or symbol parameter.
"""

SCHEMA_MD = """\
---
schema_version: 1.0
---

## Search Tools
- keywords: search, find, latest, news
- tool_name: ddg-search
- params: {"query": "extract_topic"}

## Information Lookup
- keywords: tell me about, what is, who is
- tool_name: grokipedia
- params: {"title": "extract_topic"}

## Database Tools
- keywords: sqlite, database, query
- exclude_keywords: aws, rds
- tool_name: sqlite
- params: {"query": "full_prompt"}
"""


@pytest.fixture()
def category_dir(tmp_path: Path) -> Path:
    """Populate a temp dir with synthetic category markdown files."""
    catDir = tmp_path / "categories"
    catDir.mkdir()
    (catDir / "math.md").write_text(MATH_MD)
    (catDir / "tool_calling.md").write_text(TOOL_MD)
    return catDir


@pytest.fixture()
def schema_file(tmp_path: Path) -> Path:
    """Write a synthetic schema file and return its Path."""
    schemaDir = tmp_path / "schema"
    schemaDir.mkdir()
    f = schemaDir / "information_patterns.md"
    f.write_text(SCHEMA_MD)
    return f
