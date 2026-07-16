# VideoTool

Analyse a video file: duration, FPS, frame count, and keyframe snapshots.

    Uses only the Python standard library + Pillow — no ffmpeg required.
    Supports GIF (via Pillow) and raw AVI/MP4 header parsing for metadata.
    For full frame extraction from MP4/AVI, installs gracefully with ffmpeg
    available via ShellTool; otherwise returns header-level metadata only.

**Module**: `tinytot.tools_ext`

## Constructor

```python
VideoTool(self, /, *args, **kwargs)
```

Initialize self.  See help(type(self)) for accurate signature.

## Methods

### `run(self, path: 'str', operation: 'str' = 'describe', frame_num: 'str' = '0') -> 'str'`

### `schema(self) -> 'Dict[str, Any]'`

Return an OpenAI-compatible function-tool schema dict.
