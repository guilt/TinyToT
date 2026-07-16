# `applyRefinement`

**Module**: `tinytot.refine`

## `applyRefinement`

```python
applyRefinement(intent: 'str', code: 'str', prompt: 'str' = '') -> 'Optional[str]'
```

Apply the named transformation to code and return a fenced block.

    Returns None if the intent is not a code transformation (e.g. 'explain').
