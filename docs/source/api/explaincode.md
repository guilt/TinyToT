# `explainCode`

**Module**: `tinytot.refine`

## `explainCode`

```python
explainCode(code: 'str', focus: 'Optional[str]' = None) -> 'str'
```

Produce a plain-English structural explanation of Python code.

    If focus is given (e.g. a function name), explain only that part.
    Uses ast for structure; falls back to line-by-line for non-Python.
