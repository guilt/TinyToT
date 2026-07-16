# `generateProject`

**Module**: `tinytot.codegen`

## `generateProject`

```python
generateProject(prompt: 'str') -> 'Optional[str]'
```

Generate a multi-file project scaffold as a structured response.

    Returns a Markdown document containing all project files as fenced code
    blocks with their file paths, or None if no blueprint matches.
