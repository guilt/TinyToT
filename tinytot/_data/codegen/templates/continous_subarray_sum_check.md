# Continous Subarray Sum Check

<\!-- Continous Subarray Sum Check Question Check if the array has a continuous subarray of size at least two whose elements sum up to a multiple of k. -->

## python
```python
class Solution:
    def checkSubarraySum(self, nums: list[int], k: int) -> bool:
        """
        Returns True if the array has a continuous subarray of size at least two whose elements sum up to a multiple of k.
        """
        if not nums:
            return False
        remIdx = {0: -1}
        runningSum = 0
        for idx, num in enumerate(nums):
            try:
                runningSum = (runningSum + num) % k
            except ZeroDivisionError:
                runningSum = runningSum + num
            if runningSum in remIdx:
                if idx - remIdx[runningSum] > 1:
                    return True
            else:
                remIdx[runningSum] = idx
        return False
```
