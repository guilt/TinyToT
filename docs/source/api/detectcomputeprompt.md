# `detectComputePrompt`

**Module**: `tinytot.compute`

## `detectComputePrompt`

```python
detectComputePrompt(prompt: 'str') -> 'bool'
```

Return True if the prompt appears to be a computation request.

    Checks for arithmetic expressions, unit conversions, date reasoning,
    or simple word problems before deferring to the knowledge base.
