# `generateTreeOfThoughtsResponse`

**Module**: `tinytot.inference`

## `generateTreeOfThoughtsResponse`

```python
generateTreeOfThoughtsResponse(prompt: str, categoryDir: pathlib.Path = WindowsPath('D:/WS/TinyToT/tinytot/_data/categories'), knowledgeDir: pathlib.Path = WindowsPath('D:/WS/TinyToT/tinytot/_data/knowledge'), skip_knowledge: bool = False, force_category: Union[str, NoneType] = None, direct_response: bool = False) -> str
```

Run Tree of Thoughts, grounding the best chain in knowledge when available.

    Args:
        skip_knowledge: Bypass the knowledge lookup entirely (use for code-review/debug).
        force_category: Pin to a specific category instead of auto-routing.
            Useful when the caller knows the intent (e.g. 'financial' for investment queries).
