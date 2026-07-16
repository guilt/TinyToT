# `scoreChain`

**Module**: `tinytot.retrieval`

## `scoreChain`

```python
scoreChain(prompt: 'str', chain: 'Chain', idf: 'Dict[str, float]', has_tool_result: 'bool' = False) -> 'float'
```

Return cosine similarity score for a chain against prompt.
