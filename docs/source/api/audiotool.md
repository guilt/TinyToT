# AudioTool

Analyse an audio file: duration, sample rate, channels, and speech density hint.

    Uses Python's built-in ``wave`` module for WAV files (no deps).
    For MP3/AAC/OGG, uses ffprobe when available; otherwise returns file-level metadata.
    Speech density is estimated via zero-crossing rate on the raw PCM samples —
    a high ZCR suggests speech or noisy audio; low ZCR suggests music or silence.

**Module**: `tinytot.tools_ext`

## Constructor

```python
AudioTool(self, /, *args, **kwargs)
```

Initialize self.  See help(type(self)) for accurate signature.

## Methods

### `run(self, path: 'str', operation: 'str' = 'describe') -> 'str'`

### `schema(self) -> 'Dict[str, Any]'`

Return an OpenAI-compatible function-tool schema dict.
