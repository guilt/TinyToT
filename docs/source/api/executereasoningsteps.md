# `executeReasoningSteps`

**Module**: `tinytot.inference`

## `executeReasoningSteps`

```python
executeReasoningSteps(prompt: str, category: str, chain: Tuple[str, List[str], Dict[str, Any]], context: Union[str, NoneType] = None) -> str
```

Render a chain into a readable reasoning trace.

    When `context` is provided (a knowledge passage), the chain reasons over
    that grounded content. The final conclusion is derived from the context.
    When the chain's metadata contains a 'conclusion' key (parsed from the
    category file), that text is used as the conclusion directly.
