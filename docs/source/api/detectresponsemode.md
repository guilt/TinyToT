# `detectResponseMode`

**Module**: `tinytot.inference`

## `detectResponseMode`

```python
detectResponseMode(prompt: str) -> str
```

Classify the prompt into one of four response modes.

    Priority: json_scoring > summarize > direct > reasoning_trace.
