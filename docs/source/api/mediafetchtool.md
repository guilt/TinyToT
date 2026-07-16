# MediaFetchTool

Download and preview media from URLs: YouTube, Twitter/X, Instagram, TikTok, etc.

    Uses yt-dlp for downloading.  By default fetches metadata only (no download)
    so the tool is safe to call on any URL.  Set operation='download' to save
    the media locally and return the file path for further analysis.

    Requires yt-dlp: pip install yt-dlp

**Module**: `tinytot.tools_ext`

## Constructor

```python
MediaFetchTool(self, /, *args, **kwargs)
```

Initialize self.  See help(type(self)) for accurate signature.

## Methods

### `run(self, url: 'str', operation: 'str' = 'info', output_dir: 'str' = '') -> 'str'`

### `schema(self) -> 'Dict[str, Any]'`

Return an OpenAI-compatible function-tool schema dict.
