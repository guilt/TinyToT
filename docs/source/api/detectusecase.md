# `detectUseCase`

**Module**: `tinytot.generate`

## `detectUseCase`

```python
detectUseCase(prompt: 'str') -> 'Optional[str]'
```

Return the use-case key if the prompt matches any pattern, else None.

    Checks use_cases.yaml patterns first, then falls back to checking
    howto_scripts.yaml triggers directly — so any how-to guide can be
    triggered without needing a matching use_case pattern.
