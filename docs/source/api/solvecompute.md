# `solveCompute`

**Module**: `tinytot.compute`

## `solveCompute`

```python
solveCompute(prompt: 'str') -> 'Optional[str]'
```

Attempt to solve a computation request.

    Tries (in order): unit conversion → date reasoning → word problem → arithmetic.
    Unit conversion is checked first because prompts like "what is 32F in Celsius"
    would otherwise be captured as bare arithmetic ("32").
