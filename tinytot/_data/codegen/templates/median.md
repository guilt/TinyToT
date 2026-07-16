# Median of a List

## python
```python
def median(nums: list[float]) -> float:
    """Return the median value.

    Composition: sort -> index middle element(s).
    """
    if not nums:
        raise ValueError("empty list has no median")
    sorted_nums = sorted(nums)
    n = len(sorted_nums)
    mid = n // 2
    if n % 2 == 1:
        return sorted_nums[mid]
    return (sorted_nums[mid - 1] + sorted_nums[mid]) / 2


# Or use the standard library:
# import statistics
# statistics.median([1, 3, 5])  -> 3

# Examples
print(median([3, 1, 4, 1, 5, 9, 2, 6]))  # 3.5
print(median([1, 2, 3, 4, 5]))            # 3
```

## javascript
```javascript
function median(nums) {
    const sorted = [...nums].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 1
        ? sorted[mid]
        : (sorted[mid - 1] + sorted[mid]) / 2;
}
```

## go
```go
import "sort"

func median(nums []float64) float64 {
    sorted := make([]float64, len(nums))
    copy(sorted, nums)
    sort.Float64s(sorted)
    n := len(sorted)
    if n%2 == 1 { return sorted[n/2] }
    return (sorted[n/2-1] + sorted[n/2]) / 2
}
```
