# Three Sum Closest

<\!-- 3 Sum Closest Question Given an array nums of n integers and an integer target, find three integers in nums such that the sum is closest to target. -->

## python
```python
from typing import List

class Solution:
    def threeSumClosest(self, numList: List[int], targetSum: int) -> int:
        numList.sort()
        closestSum = float('inf')
        for index in range(len(numList) - 2):
            leftPointer, rightPointer = index + 1, len(numList) - 1
            while leftPointer < rightPointer:
                currentSum = numList[index] + numList[leftPointer] + numList[rightPointer]
                if abs(targetSum - currentSum) < abs(targetSum - closestSum):
                    closestSum = currentSum
                if currentSum < targetSum:
                    leftPointer += 1
                else:
                    rightPointer -= 1
        return closestSum
```
