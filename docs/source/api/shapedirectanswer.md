# `shapeDirectAnswer`

**Module**: `tinytot.inference`

## `shapeDirectAnswer`

```python
shapeDirectAnswer(prompt: str, passage: str, idf: Union[dict, NoneType] = None) -> str
```

Trim a knowledge passage to match the brevity level requested in the prompt.

    - one word     → the highest-IDF term in the passage that does not appear in
                     the prompt, i.e. the new information the passage introduces
    - one sentence → first sentence of the passage
    - otherwise    → full passage
