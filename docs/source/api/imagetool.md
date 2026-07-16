# ImageTool

Analyse an image file: dimensions, colour palette, pixel stats, and embedded text.

    This is TinyToT's deterministic first pass — no neural weights required.
    It uses Pillow for pixel analysis and a simple frequency-based OCR heuristic
    to surface large text regions.  For full vision / OCR, wire an external model.

**Module**: `tinytot.tools_ext`

## Constructor

```python
ImageTool(self, /, *args, **kwargs)
```

Initialize self.  See help(type(self)) for accurate signature.

## Methods

### `run(self, path: 'str', operation: 'str' = 'describe') -> 'str'`

### `schema(self) -> 'Dict[str, Any]'`

Return an OpenAI-compatible function-tool schema dict.
