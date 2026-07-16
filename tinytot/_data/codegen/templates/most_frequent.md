# Most Frequent Element

## python
```python
from collections import Counter


def most_frequent(items: list):
    """Return the most frequently occurring element.

    Composition: count frequencies (Counter) + find max by value.
    """
    if not items:
        raise ValueError("empty list")
    counts = Counter(items)
    return counts.most_common(1)[0][0]


def top_k_frequent(items: list, k: int) -> list:
    """Return the k most frequent elements (in order of frequency)."""
    counts = Counter(items)
    return [item for item, _ in counts.most_common(k)]


def mode(numbers: list[float]) -> float:
    """Statistical mode (most common value in a dataset)."""
    return most_frequent(numbers)


# Examples
print(most_frequent([1, 2, 2, 3, 3, 3, 4]))    # 3
print(top_k_frequent([1, 2, 2, 3, 3, 3], 2))   # [3, 2]
print(most_frequent(["apple", "banana", "apple"]))  # "apple"
```

## javascript
```javascript
function mostFrequent(items) {
    const counts = {};
    for (const item of items) counts[item] = (counts[item] || 0) + 1;
    return Object.entries(counts).reduce((a, b) => a[1] > b[1] ? a : b)[0];
}
```

## go
```go
func mostFrequent(items []int) int {
    counts := make(map[int]int)
    for _, v := range items { counts[v]++ }
    best, bestCount := 0, 0
    for k, v := range counts {
        if v > bestCount { best = k; bestCount = v }
    }
    return best
}
```
