# `detectToolUsage`

**Module**: `tinytot.tools`

## `detectToolUsage`

```python
detectToolUsage(prompt: 'str', schemaFile: 'Path' = WindowsPath('D:/WS/TinyToT/tinytot/_data/schema/information_patterns.md')) -> 'Tuple[Optional[str], Dict[str, Any]]'
```

Return (tool_name, params) if prompt matches a schema tool pattern, else (None, {}).
