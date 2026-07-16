# Longest Common Subsequence (LCS)

## python
```python
def lcs_length(s1: str, s2: str) -> int:
    """Return the length of the longest common subsequence. O(m*n) time."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]


def lcs_string(s1: str, s2: str) -> str:
    """Return the actual longest common subsequence string."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    # Backtrack to recover the string
    result = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i-1] == s2[j-1]:
            result.append(s1[i-1])
            i -= 1; j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(result))


# Examples
print(lcs_length("ABCBDAB", "BDCAB"))  # 4
print(lcs_string("ABCBDAB", "BDCAB"))  # "BCAB" or "BDAB"
```

## javascript
```javascript
function lcsLength(s1, s2) {
    const m = s1.length, n = s2.length;
    const dp = Array.from({length: m+1}, () => new Array(n+1).fill(0));
    for (let i = 1; i <= m; i++)
        for (let j = 1; j <= n; j++)
            dp[i][j] = s1[i-1] === s2[j-1]
                ? dp[i-1][j-1] + 1
                : Math.max(dp[i-1][j], dp[i][j-1]);
    return dp[m][n];
}
```

## go
```go
func lcsLength(s1, s2 string) int {
    m, n := len(s1), len(s2)
    dp := make([][]int, m+1)
    for i := range dp { dp[i] = make([]int, n+1) }
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
            } else if dp[i-1][j] > dp[i][j-1] {
                dp[i][j] = dp[i-1][j]
            } else {
                dp[i][j] = dp[i][j-1]
            }
        }
    }
    return dp[m][n]
}
```
