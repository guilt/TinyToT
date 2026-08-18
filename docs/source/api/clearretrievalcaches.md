# `clearRetrievalCaches`

**Module**: `tinytot.retrieval`

## `clearRetrievalCaches`

```python
clearRetrievalCaches() -> 'None'
```

Clear all retrieval-layer lru_caches (indexes built on top of content).

After calling this (and content.clearContentCaches), the next query will
rebuild the TF-IDF / multi-head indexes from the freshly loaded passages
and chains.
