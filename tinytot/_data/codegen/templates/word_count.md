# Word Count

## python
```python
def word_count(text: str) -> dict[str, int]:
    """Count word frequencies in text (case-insensitive)."""
    words = text.lower().split()
    counts: dict[str, int] = {}
    for word in words:
        # Strip punctuation
        word = word.strip(".,!?;:\"'()-")
        if word:
            counts[word] = counts.get(word, 0) + 1
    return counts


# Or use Counter from collections:
# from collections import Counter
# return Counter(text.lower().split())

text = "the quick brown fox jumps over the lazy dog the fox"
print(word_count(text))
# {'the': 3, 'quick': 1, 'brown': 1, 'fox': 2, ...}
```
