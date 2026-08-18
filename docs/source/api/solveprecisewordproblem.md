# `solvePreciseWordProblem`

**Module**: `tinytot.compute`

## `solvePreciseWordProblem`

```python
solvePreciseWordProblem(prompt: 'str') -> 'Optional[str]'
```

Solve only structurally-anchored word-problem classes.

Precision-first: each class requires complete anchors (clock times, speeds,
distances) so it cannot misfire on partial numeric prose.  Broad prose word
problems are deliberately NOT attempted here — the permissive solvers are
wrong on ~95% of real prose, so those fall through to the knowledge base /
reasoning pipeline instead.
