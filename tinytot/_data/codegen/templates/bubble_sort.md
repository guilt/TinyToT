# Bubble Sort

## python
```python
def bubble_sort(arr: list) -> list:
    """Sort arr using bubble sort. O(n²) time — use only for teaching."""
    arr = list(arr)  # copy to avoid mutating input
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break  # already sorted
    return arr


print(bubble_sort([5, 3, 8, 1, 2]))  # [1, 2, 3, 5, 8]
```
