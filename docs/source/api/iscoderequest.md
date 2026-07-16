# `isCodeRequest`

**Module**: `tinytot.codegen`

## `isCodeRequest`

```python
isCodeRequest(prompt: 'str') -> 'bool'
```

Return True if the prompt is asking for code to be written.

    Uses request_patterns from config.yaml, plus any template pattern match.
