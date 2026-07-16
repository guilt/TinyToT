# Flatten

## python
```python
def flatten(nested: list) -> list:
    """Flatten a nested list of arbitrary depth."""
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


# Example
print(flatten([1, [2, 3], [4, [5, 6]]]))  # [1, 2, 3, 4, 5, 6]

# One-level flatten with a list comprehension:
shallow = [x for sublist in [[1, 2], [3, 4]] for x in sublist]
```
