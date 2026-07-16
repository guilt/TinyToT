# `categorizePrompt`

**Module**: `tinytot.retrieval`

## `categorizePrompt`

```python
categorizePrompt(prompt: 'str', categoryDir: 'Path' = WindowsPath('D:/WS/TinyToT/tinytot/_data/categories')) -> 'str'
```

Return best-matching category name via TF-IDF cosine similarity.

    Uses the proven single-head TF-IDF approach for routing — multi-head
    scoring is applied to knowledge passage retrieval (findKnowledgeAnswer)
    where it improves precision, but routing accuracy is already 100% with
    single-head TF-IDF + keyword repeat boosting and multi-head adds noise.
