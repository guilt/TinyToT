# `chainVector`

**Module**: `tinytot.retrieval`

## `chainVector`

```python
chainVector(title: 'str', thoughts: 'List[str]', idf: 'Dict[str, float]') -> 'Dict[str, float]'
```

Build a unit-norm TF-IDF vector for a single chain (title + thoughts).
