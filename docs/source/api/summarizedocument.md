# `summarizeDocument`

**Module**: `tinytot.summarize`

## `summarizeDocument`

```python
summarizeDocument(text: 'str', max_words: 'int' = 50, chunk_size: 'int' = 150, inter_words: 'int' = 80) -> 'str'
```

Summarise *text* to at most *max_words* words using extractive TF-IDF.

    For short texts (< ARC_THRESHOLD sentences) standard extractive selection is used.
    For long texts (novels, reports) arc-aware election picks the best sentence from
    each narrative quarter (setup / rising / climax / resolution) and stitches them
    into a flowing prose summary.

    Args:
        text:       Full document text.
        max_words:  Word budget for the final summary.
        chunk_size: Unused (kept for API compatibility).
        inter_words: Unused (kept for API compatibility).

    Returns:
        Summary string of at most *max_words* words.


**Examples**


```python
text = open("lotr.txt").read()
print(summarizeDocument(text, max_words=50))
```
