# `multiHeadScore`

**Module**: `tinytot.retrieval`

## `multiHeadScore`

```python
multiHeadScore(query: 'str', chain_title: 'str', chain_thoughts: 'List[str]', chain_conclusion: 'str', chain_keywords: 'str', idf: 'Dict[str, float]', avg_doc_len: 'float') -> 'float'
```

Compute a weighted multi-head similarity score between query and a chain.

    Aggregates five independent scoring heads:
      H1  TF-IDF cosine on title+thoughts
      H2  TF-IDF cosine on conclusion text
      H3  Character trigram cosine
      H4  BM25 on title+thoughts tokens
      H5  Keyword frontmatter exact token hit rate
