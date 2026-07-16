# `buildContextPrompt`

**Module**: `tinytot.inference`

## `buildContextPrompt`

```python
buildContextPrompt(messages: list, current: str) -> str
```

Build an enriched prompt by prepending relevant prior conversation turns.

    Rules:
    - If current message is a short follow-up (elaboration request), prepend
      the last assistant response as context so the intent is recoverable.
    - If current message is a direct answer to a clarification question, prepend
      the clarification question so the compound query is answerable.
    - Otherwise append recent user turns as context (last 2 exchanges max).
