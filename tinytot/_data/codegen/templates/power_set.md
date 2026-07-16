# Power Set (All Subsets)

## python
```python
def power_set(items: list) -> list[list]:
    """Return all subsets of items (2^n subsets total).

    Composition: each element is either included or excluded (binary recursion).
    """
    if not items:
        return [[]]
    first, rest = items[0], items[1:]
    subsets_without = power_set(rest)
    subsets_with = [[first] + s for s in subsets_without]
    return subsets_without + subsets_with


def power_set_iterative(items: list) -> list[list]:
    """Iterative version using bitmask. O(2^n * n) time."""
    n = len(items)
    result = []
    for mask in range(1 << n):   # 0 to 2^n - 1
        subset = [items[i] for i in range(n) if mask & (1 << i)]
        result.append(subset)
    return result


# Examples
print(power_set([1, 2, 3]))
# [[], [3], [2], [2,3], [1], [1,3], [1,2], [1,2,3]]

print(power_set_iterative([1, 2, 3]))
# [[], [1], [2], [1,2], [3], [1,3], [2,3], [1,2,3]]

print(f"Total subsets: {2 ** 3}")  # 8
```

## javascript
```javascript
function powerSet(items) {
    if (items.length === 0) return [[]];
    const [first, ...rest] = items;
    const subsetsWithout = powerSet(rest);
    const subsetsWith = subsetsWithout.map(s => [first, ...s]);
    return [...subsetsWithout, ...subsetsWith];
}

console.log(powerSet([1, 2, 3]).length); // 8
```
