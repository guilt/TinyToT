# `summarizeFile`

**Module**: `tinytot.summarize`

## `summarizeFile`

```python
summarizeFile(path: 'str | Path', max_words: 'int' = 50, encoding: 'str' = 'utf-8') -> 'str'
```

Read a file from *path* and return a *max_words*-word extractive summary.

    Args:
        path:      Path to any plain-text file (.txt, .md, .rst, etc.).
        max_words: Word budget for the final summary.
        encoding:  File encoding (default utf-8).

    Returns:
        Summary string of at most *max_words* words, or an error message.
