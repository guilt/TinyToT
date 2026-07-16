# `scoreResponse`

**Module**: `tinytot.retrieval`

## `scoreResponse`

```python
scoreResponse(response_text: 'str', knowledgeDir: 'Path' = WindowsPath('D:/WS/TinyToT/tinytot/_data/knowledge')) -> 'float'
```

Score a text against the knowledge base, returning a float in [0.0, 1.0].

    Normalises the raw cosine similarity so that:
    - A response at or above KNOWLEDGE_DIRECT_THRESHOLD scores near 1.0
    - A response at KNOWLEDGE_THRESHOLD scores around 0.5
    - A response below KNOWLEDGE_THRESHOLD scores 0.0

    This gives the LLM judge scorers a meaningful gradient rather than raw
    similarity values that would always be well below 1.0 for realistic text.
