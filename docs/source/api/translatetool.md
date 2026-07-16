# TranslateTool

Translate text between languages using deep-translator (Google backend, free).

**Module**: `tinytot.tools_ext`

## Constructor

```python
TranslateTool(self, /, *args, **kwargs)
```

Initialize self.  See help(type(self)) for accurate signature.

## Methods

### `run(self, text: 'str', target: 'str' = 'en', source: 'str' = 'auto') -> 'str'`

Translate text through a backend fallback chain.

        Backends tried in order:
          1. argostranslate — fully offline Python library, no network after pack install.
             Install packs: python -m argostranslate.package --install en ko
             LibreTranslate uses this same engine internally.
          2. LibreTranslate HTTP (local) — if running at LIBRETRANSLATE_URL (default
             http://localhost:5000). Start with: pip install libretranslate && libretranslate
          3. Google Translate free endpoint via httpx (proxy-aware, HTTP_PROXY/SOCKS).
          4. MyMemory free API via httpx.
          5. Graceful no-op — returns original text with a helpful message.

### `schema(self) -> 'Dict[str, Any]'`

Return an OpenAI-compatible function-tool schema dict.
