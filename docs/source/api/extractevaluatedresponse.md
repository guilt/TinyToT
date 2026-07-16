# `extractEvaluatedResponse`

**Module**: `tinytot.inference`

## `extractEvaluatedResponse`

```python
extractEvaluatedResponse(prompt: str) -> str
```

Pull out the text under a 'Response:' label in a scoring prompt.

    Falls back to the full prompt if no such label is found.
