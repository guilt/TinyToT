# Find Min

## python
```python
def find_min(numbers: list) -> float:
    """Return the minimum value in a list. O(n) time."""
    if not numbers:
        raise ValueError("cannot find min of empty list")
    minimum = numbers[0]
    for n in numbers[1:]:
        if n < minimum:
            minimum = n
    return minimum


print(find_min([3, 1, 4, 1, 5, 9, 2, 6]))  # 1
```
