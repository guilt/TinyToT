# Knapsack 0/1

## python
```python
def knapsack(weights: list[int], values: list[int], capacity: int) -> int:
    """Return the maximum value achievable within the weight capacity.

    0/1 knapsack: each item is either taken (1) or left (0).
    O(n * capacity) time and space.
    """
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Option 1: skip item i
            dp[i][w] = dp[i-1][w]
            # Option 2: take item i (if it fits)
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w - weights[i-1]] + values[i-1])
    return dp[n][capacity]


def knapsack_items(weights: list[int], values: list[int], capacity: int) -> tuple[int, list[int]]:
    """Return (max_value, list_of_chosen_item_indices)."""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w - weights[i-1]] + values[i-1])
    # Backtrack to find chosen items
    chosen = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            chosen.append(i - 1)
            w -= weights[i-1]
    return dp[n][capacity], list(reversed(chosen))


# Example
weights = [2, 3, 4, 5]
values  = [3, 4, 5, 6]
capacity = 8
print(knapsack(weights, values, capacity))         # 10  (items 1+2: weight 5, value 7? No: items 0+3: 2+5=7 cap, 3+6=9. items 1+3: 3+5=8, 4+6=10)
max_val, items = knapsack_items(weights, values, capacity)
print(f"Max value: {max_val}, items: {items}")
```

## javascript
```javascript
function knapsack(weights, values, capacity) {
    const n = weights.length;
    const dp = Array.from({length: n+1}, () => new Array(capacity+1).fill(0));
    for (let i = 1; i <= n; i++) {
        for (let w = 0; w <= capacity; w++) {
            dp[i][w] = dp[i-1][w];
            if (weights[i-1] <= w)
                dp[i][w] = Math.max(dp[i][w], dp[i-1][w-weights[i-1]] + values[i-1]);
        }
    }
    return dp[n][capacity];
}
```

## go
```go
func knapsack(weights, values []int, capacity int) int {
    n := len(weights)
    dp := make([][]int, n+1)
    for i := range dp { dp[i] = make([]int, capacity+1) }
    for i := 1; i <= n; i++ {
        for w := 0; w <= capacity; w++ {
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w {
                v := dp[i-1][w-weights[i-1]] + values[i-1]
                if v > dp[i][w] { dp[i][w] = v }
            }
        }
    }
    return dp[n][capacity]
}
```
