# Find Duplicates

## python
```python
def find_duplicates(nums: list) -> list:
    """Return list of elements that appear more than once.

    Composition: count frequencies, filter where count > 1.
    """
    from collections import Counter
    counts = Counter(nums)
    return [item for item, count in counts.items() if count > 1]


def find_duplicates_inplace(nums: list[int]) -> list[int]:
    """Find duplicates in O(n) time O(1) extra space using index negation.
    Works when all values are in range [1, len(nums)].
    """
    result = []
    for num in nums:
        idx = abs(num) - 1
        if nums[idx] < 0:
            result.append(abs(num))
        else:
            nums[idx] = -nums[idx]
    # Restore the array
    for i in range(len(nums)):
        nums[i] = abs(nums[i])
    return result


def remove_duplicates(nums: list) -> list:
    """Return a new list with duplicates removed, preserving order."""
    seen = set()
    result = []
    for n in nums:
        if n not in seen:
            seen.add(n)
            result.append(n)
    return result


# Examples
print(find_duplicates([4, 3, 2, 7, 8, 2, 3, 1]))   # [2, 3]
print(remove_duplicates([1, 2, 2, 3, 3, 4]))        # [1, 2, 3, 4]
```

## javascript
```javascript
function findDuplicates(nums) {
    const counts = {};
    for (const n of nums) counts[n] = (counts[n] || 0) + 1;
    return Object.keys(counts).filter(k => counts[k] > 1).map(Number);
}

function removeDuplicates(nums) {
    return [...new Set(nums)];
}
```

## go
```go
func findDuplicates(nums []int) []int {
    count := make(map[int]int)
    for _, n := range nums { count[n]++ }
    var result []int
    for k, v := range count {
        if v > 1 { result = append(result, k) }
    }
    return result
}
```
