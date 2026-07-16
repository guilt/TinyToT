# Tool

Base class for all TinyToT agent tools.

**Module**: `tinytot.tools_ext`

## Constructor

```python
Tool(self, /, *args, **kwargs)
```

Initialize self.  See help(type(self)) for accurate signature.

## Methods

### `run(self, **kwargs: 'Any') -> 'str'`

Execute the tool and return a plain-text result.

### `schema(self) -> 'Dict[str, Any]'`

Return an OpenAI-compatible function-tool schema dict.
