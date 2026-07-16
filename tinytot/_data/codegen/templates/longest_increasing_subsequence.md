# Longest Increasing Subsequence

<\!-- Longest Increasing Subsequence Question Given an array of integers, find the length of the longest increasing subsequence. -->

## python
```python
from bisect import bisect_left
from typing import List

class Solution:
    def longestIncreasingSubsequence(self, numberList: List[int]) -> int:
        """
        Returns the length of the longest increasing subsequence in numberList.
        """
        if not numberList:
            return 0
        subsequenceTails = []
        for value in numberList:
            position = bisect_left(subsequenceTails, value)
            if position == len(subsequenceTails):
                subsequenceTails.append(value)
            else:
                subsequenceTails[position] = value
        return len(subsequenceTails)
```
