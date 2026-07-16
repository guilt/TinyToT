# `findKnowledgeAnswer`

**Module**: `tinytot.retrieval`

## `findKnowledgeAnswer`

```python
findKnowledgeAnswer(prompt: 'str', knowledgeDir: 'Path' = WindowsPath('D:/WS/TinyToT/tinytot/_data/knowledge')) -> 'Optional[Tuple[str, float]]'
```

Return (passage, score) if a knowledge passage scores above KNOWLEDGE_THRESHOLD.

    Two-stage retrieval:
      Stage 1 (coarse): TF-IDF cosine over all passages — fast O(N) scan to
                        select the top-K candidates.
      Stage 2 (rerank): Multi-head scoring on the top-K candidates — applies
                        BM25, trigram, conclusion, and keyword heads for precision.

    This mirrors how production retrieval systems work: ANN index for recall,
    cross-encoder re-ranker for precision.
