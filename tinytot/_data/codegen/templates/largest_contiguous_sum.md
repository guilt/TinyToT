# Largest Contiguous Sum

<\!-- Largest Contiguous Sum (Kadane’s Algorithm) Question Given an integer array, find the contiguous subarray with the largest sum (Kadane’s Algorithm). -->

## python
```python
class Solution:
    def largestContiguousSum(self, numberList: list[int]) -> int:
        """
        Returns the largest sum of a contiguous subarray using Kadane's Algorithm.
        """
        maxSoFar = float('-inf')
        maxEndingHere = 0
        for value in numberList:
            maxEndingHere = max(value, maxEndingHere + value)
            maxSoFar = max(maxSoFar, maxEndingHere)
        return maxSoFar
```
