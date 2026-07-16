# Equal Partition Possible

<\!-- Equal Partition Possible? Question Given an array of integers, determine if it can be partitioned into two subsets with equal sum. Example Input: nums -->

## python
```python
class Solution:
    def canPartition(self, numList: list[int]) -> bool:
        """
        Determines if the list can be partitioned into two subsets with equal sum.
        """
        totalSum = sum(numList)
        if totalSum % 2 != 0:
            return False
        targetSum = totalSum // 2
        dp = [False] * (targetSum + 1)
        dp[0] = True
        for num in numList:
            for j in range(targetSum, num - 1, -1):
                dp[j] = dp[j] or dp[j - num]
        return dp[targetSum]
```
