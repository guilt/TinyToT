# Climb Stairs (Ways to Reach Step N)

## python
```python
def climb_stairs(n: int) -> int:
    """Return number of ways to climb n stairs taking 1 or 2 steps at a time.

    This is Fibonacci(n+1). O(n) time, O(1) space.
    """
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


def climb_stairs_k_steps(n: int, k: int) -> int:
    """Return number of ways to climb n stairs with steps 1..k."""
    dp = [0] * (n + 1)
    dp[0] = 1
    for i in range(1, n + 1):
        for step in range(1, min(k, i) + 1):
            dp[i] += dp[i - step]
    return dp[n]


# Examples
print(climb_stairs(5))              # 8  (Fibonacci(6))
print(climb_stairs_k_steps(5, 3))   # 13 (steps 1,2,3 allowed)
```

## javascript
```javascript
function climbStairs(n) {
    if (n <= 2) return n;
    let [a, b] = [1, 2];
    for (let i = 3; i <= n; i++) [a, b] = [b, a + b];
    return b;
}

console.log(climbStairs(5)); // 8
```

## go
```go
func climbStairs(n int) int {
    if n <= 2 { return n }
    a, b := 1, 2
    for i := 3; i <= n; i++ { a, b = b, a+b }
    return b
}
```

## rust
```rust
fn climb_stairs(n: u32) -> u64 {
    if n <= 2 { return n as u64; }
    let (mut a, mut b) = (1u64, 2u64);
    for _ in 3..=n { let c = a + b; a = b; b = c; }
    b
}
```
