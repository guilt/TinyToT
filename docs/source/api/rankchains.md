# `rankChains`

**Module**: `tinytot.retrieval`

## `rankChains`

```python
rankChains(prompt: 'str', chains: 'List[Chain]', idf: 'Dict[str, float]') -> 'List[Tuple[Chain, float]]'
```

Return chains sorted by descending score, capped at MAX_EVALUATED_PATHS.

    Greedy fast-path: if exactly one chain scores non-zero, skip full sort.
