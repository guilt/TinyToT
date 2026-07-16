# Find Max

## python
```python
def find_max(numbers: list) -> float:
    """Return the maximum value in a list. O(n) time."""
    if not numbers:
        raise ValueError("cannot find max of empty list")
    maximum = numbers[0]
    for n in numbers[1:]:
        if n > maximum:
            maximum = n
    return maximum


# Or simply: max(numbers)

print(find_max([3, 1, 4, 1, 5, 9, 2, 6]))  # 9
```
