# `generateJsonScoringResponse`

**Module**: `tinytot.inference`

## `generateJsonScoringResponse`

```python
generateJsonScoringResponse(prompt: str, knowledgeDir: pathlib._local.Path = Path('tinytot/_data/knowledge')) -> str
```

Score the response embedded in a scoring prompt and return a JSON string.

Extracts the evaluated text, scores it against the knowledge base via
cosine similarity, and returns {"score": float, "rationale": str}.
