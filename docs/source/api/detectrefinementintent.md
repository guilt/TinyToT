# `detectRefinementIntent`

**Module**: `tinytot.refine`

## `detectRefinementIntent`

```python
detectRefinementIntent(prompt: 'str') -> 'Optional[str]'
```

Return a refinement intent key if the prompt is modifying a prior response.

    Returns None if this looks like a fresh request.
