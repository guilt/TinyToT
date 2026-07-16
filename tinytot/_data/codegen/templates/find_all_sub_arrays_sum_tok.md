# Find All Sub Arrays Sum Tok

<\!-- Find All SubArrays that add to a SubArray Sum == k Question Given an array of integers and an integer k, find the total number of continuous subarrays -->

## python
```python
class Solution:
    def subarraySum(self, numList: list[int], targetSum: int) -> int:
        """
        Returns the total number of continuous subarrays whose sum equals to k.
        """
        totalCount = 0
        runningSum = 0
        prefixSumCounts = {0: 1}
        for number in numList:
            runningSum += number
            if runningSum - targetSum in prefixSumCounts:
                totalCount += prefixSumCounts[runningSum - targetSum]
            prefixSumCounts[runningSum] = prefixSumCounts.get(runningSum, 0) + 1
        return totalCount
```
