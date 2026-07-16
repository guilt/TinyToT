# DocumentTool

Extract text from PDF, DOCX, TXT, or Markdown files (local path or URL).

**Module**: `tinytot.tools_ext`

## Constructor

```python
DocumentTool(self, /, *args, **kwargs)
```

Initialize self.  See help(type(self)) for accurate signature.

## Methods

### `run(self, source: 'str', max_chars: 'str' = '8000', pages: 'str' = '') -> 'str'`

### `schema(self) -> 'Dict[str, Any]'`

Return an OpenAI-compatible function-tool schema dict.
