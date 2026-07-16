# Subset Sum

<\!-- Subset Sum Question Given an array of integers and a target sum, determine if there is a subset of the array that sums to the target. Example Input: n -->

## python
```python
class Solution:
    def canPartition(self, nums: list[int], target: int) -> bool:
        """
        Returns True if there exists a subset of nums that sums to target.
        Uses dynamic programming.
        """
        n = len(nums)
        dp = [[False] * (target + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = True
        for i in range(1, n + 1):
            for j in range(1, target + 1):
                if nums[i - 1] > j:
                    dp[i][j] = dp[i - 1][j]
                else:
                    dp[i][j] = dp[i - 1][j] or dp[i - 1][j - nums[i - 1]]
        return dp[n][target]
```
