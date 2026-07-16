# `generateReasoningResponse`

**Module**: `tinytot.inference`

## `generateReasoningResponse`

```python
generateReasoningResponse(prompt: str, categoryDir: pathlib.Path = WindowsPath('D:/WS/TinyToT/tinytot/_data/categories'), knowledgeDir: pathlib.Path = WindowsPath('D:/WS/TinyToT/tinytot/_data/knowledge'), session_id: str = '', history: Union[list, NoneType] = None) -> str
```

Dispatch to the appropriate response generator based on prompt intent.

    Dispatch order (each stage exits early if it produces an answer):
      1. json_scoring    — structured score/rationale JSON
      2. summarize       — extractive summarization of long text
      3. compute         — arithmetic, unit conversion, date math
      4. agent           — plan-execute loop for prompts needing tools
                           (web, documents, files, shell, images, translate, data)
      5. knowledge_first — try the knowledge base for ANY short query before
                           committing to a reasoning mode; high-confidence hits
                           (>= KNOWLEDGE_DIRECT_THRESHOLD) are returned directly,
                           moderate hits (>= KNOWLEDGE_DIRECT_LOWER) shape the
                           direct answer, and yes/no hits are answered inline.
      6. reasoning_trace — Tree of Thoughts with knowledge grounding fallback
