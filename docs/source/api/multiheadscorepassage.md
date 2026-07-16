# `multiHeadScorePassage`

**Module**: `tinytot.retrieval`

## `multiHeadScorePassage`

```python
multiHeadScorePassage(query: 'str', heading: 'str', passage: 'str', idf: 'Dict[str, float]', avg_doc_len: 'float', source_weight: 'float' = 1.0) -> 'float'
```

Multi-head similarity score for a knowledge passage.

    Same five heads as chain scoring, adapted for passage retrieval:
      H1  TF-IDF cosine on heading+passage
      H2  TF-IDF cosine on passage only (no heading)
      H3  Character trigram cosine
      H4  BM25 on passage tokens
      H5  Heading token overlap with query (exact match signal)
