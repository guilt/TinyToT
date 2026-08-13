# `clearContentCaches`

**Module**: `tinytot.content`

## `clearContentCaches`

```python
clearContentCaches() -> 'None'
```

Clear all content-layer lru_caches so the next call reloads from disk.

    Call this (and the corresponding retrieval clear) after editing knowledge
    or category files if you want the changes to take effect without restarting
    the server.
