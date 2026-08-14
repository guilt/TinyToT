# `categorizePrompt`

**Module**: `tinytot.retrieval`

## `categorizePrompt`

```python
categorizePrompt(prompt: 'str', categoryDir: 'Path' = WindowsPath('D:/WS/TinyToT/tinytot/_data/categories')) -> 'str'
```

Return best-matching category name via TF-IDF cosine similarity.

    Uses the proven single-head TF-IDF approach for routing — multi-head
    scoring is applied to knowledge passage retrieval (findKnowledgeAnswer)
    where it improves precision, but routing accuracy is already high with
    single-head TF-IDF + keyword repeat boosting and multi-head adds noise.

    Relative-motion rate problems (speeds in mph/km/h) are routed to the
    ``math`` category when one exists: TF-IDF otherwise scatters them onto
    unrelated chains (e.g. ``agent``), producing nonsense reasoning traces.
