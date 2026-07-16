# Second Largest

## python
```python
def second_largest(nums: list[int]) -> int:
    """Return the second largest distinct value.

    Composition: sort descending, find first element != largest.
    Or: single pass with two variables.
    """
    if len(nums) < 2:
        raise ValueError("need at least 2 elements")
    first = second = float('-inf')
    for n in nums:
        if n > first:
            second = first
            first = n
        elif n > second and n != first:
            second = n
    if second == float('-inf'):
        raise ValueError("no second distinct largest element")
    return second


# Alternative: sort-based (simpler, O(n log n))
def second_largest_sort(nums: list[int]) -> int:
    unique = sorted(set(nums), reverse=True)
    if len(unique) < 2:
        raise ValueError("no second distinct largest element")
    return unique[1]


# Examples
print(second_largest([3, 1, 4, 1, 5, 9, 2, 6]))  # 6
print(second_largest([5, 5, 5]))                  # ValueError
```

## javascript
```javascript
function secondLargest(nums) {
    let first = -Infinity, second = -Infinity;
    for (const n of nums) {
        if (n > first) { second = first; first = n; }
        else if (n > second && n !== first) { second = n; }
    }
    return second === -Infinity ? null : second;
}
```

## go
```go
import "math"

func secondLargest(nums []int) (int, bool) {
    first, second := math.MinInt, math.MinInt
    for _, n := range nums {
        if n > first { second = first; first = n } else if n > second && n != first { second = n }
    }
    return second, second != math.MinInt
}
```
