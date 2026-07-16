# ShellTool

Run a shell command and return stdout + stderr.

**Module**: `tinytot.tools_ext`

## Constructor

```python
ShellTool(self, /, *args, **kwargs)
```

Initialize self.  See help(type(self)) for accurate signature.

## Methods

### `run(self, command: 'str', cwd: 'str' = '', timeout: 'str' = '30') -> 'str'`

### `schema(self) -> 'Dict[str, Any]'`

Return an OpenAI-compatible function-tool schema dict.
