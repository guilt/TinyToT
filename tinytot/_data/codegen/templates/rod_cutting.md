# Rod Cutting

<\!-- Rod Cutting Question Given a rod of length n and a list of prices for each length, determine the maximum revenue you can obtain by cutting the rod and -->

## python
```python
class Solution:
    def rodCutting(self, length, prices):
        """
        Returns the maximum revenue obtainable by cutting the rod and selling the pieces.
        """
        n = len(length)
        dp = [0] * (n + 1)
        for i in range(1, n + 1):
            for j in range(i, n + 1):
                dp[j] = max(dp[j], dp[j - i] + prices[i - 1])
        return dp[n]
```
