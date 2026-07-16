# Coin Change (Minimum Coins)

## python
```python
def coin_change(coins: list[int], amount: int) -> int:
    """Return the minimum number of coins to make amount. -1 if impossible.

    Classic dynamic programming (bottom-up). O(amount * len(coins)) time.
    """
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for a in range(1, amount + 1):
        for coin in coins:
            if coin <= a:
                dp[a] = min(dp[a], dp[a - coin] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1


def coin_change_ways(coins: list[int], amount: int) -> int:
    """Return the number of distinct combinations to make amount."""
    dp = [0] * (amount + 1)
    dp[0] = 1
    for coin in coins:
        for a in range(coin, amount + 1):
            dp[a] += dp[a - coin]
    return dp[amount]


# Examples
print(coin_change([1, 5, 10, 25], 41))  # 4  (25+10+5+1)
print(coin_change([2], 3))              # -1 (impossible)
print(coin_change_ways([1, 2, 5], 5))   # 4  (5, 2+2+1, 2+1+1+1, 1+1+1+1+1)
```

## javascript
```javascript
function coinChange(coins, amount) {
    const dp = new Array(amount + 1).fill(Infinity);
    dp[0] = 0;
    for (let a = 1; a <= amount; a++) {
        for (const coin of coins) {
            if (coin <= a) dp[a] = Math.min(dp[a], dp[a - coin] + 1);
        }
    }
    return dp[amount] === Infinity ? -1 : dp[amount];
}
```

## go
```go
func coinChange(coins []int, amount int) int {
    dp := make([]int, amount+1)
    for i := range dp { dp[i] = amount + 1 }
    dp[0] = 0
    for a := 1; a <= amount; a++ {
        for _, c := range coins {
            if c <= a && dp[a-c]+1 < dp[a] {
                dp[a] = dp[a-c] + 1
            }
        }
    }
    if dp[amount] > amount { return -1 }
    return dp[amount]
}
```

## rust
```rust
fn coin_change(coins: &[u32], amount: u32) -> i32 {
    let n = amount as usize;
    let mut dp = vec![i32::MAX; n + 1];
    dp[0] = 0;
    for a in 1..=n {
        for &c in coins {
            let c = c as usize;
            if c <= a && dp[a - c] != i32::MAX {
                dp[a] = dp[a].min(dp[a - c] + 1);
            }
        }
    }
    if dp[n] == i32::MAX { -1 } else { dp[n] }
}
```
