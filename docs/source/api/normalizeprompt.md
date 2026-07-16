# `normalizePrompt`

**Module**: `tinytot.inference`

## `normalizePrompt`

```python
normalizePrompt(prompt: str) -> str
```

Expand contractions and normalize whitespace/punctuation for better TF-IDF matching.

    This improves routing accuracy for conversational inputs. The compute path
    in particular benefits since its regexes expect 'what is' not 'what's'.
