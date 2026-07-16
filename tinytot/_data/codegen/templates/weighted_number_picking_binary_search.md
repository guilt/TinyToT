# Weighted Number Picking Binary Search

<\!-- Weighted Number Picking with Binary Search Question Pick an index randomly with probability proportional to its weight. -->

## python
```python
import random
from typing import List

class Solution:
    def __init__(self, weightList: List[int]):
        self.prefixSumList = []
        runningPrefixSum = 0
        for weight in weightList:
            runningPrefixSum += weight
            self.prefixSumList.append(runningPrefixSum)
        self.totalWeightSum = runningPrefixSum

    def pickIndex(self) -> int:
        """
        Returns an index randomly with probability proportional to its weight.
        """
        targetValue = random.randint(1, self.totalWeightSum)
        leftPointer, rightPointer = 0, len(self.prefixSumList) - 1
        while leftPointer < rightPointer:
            middlePointer = (leftPointer + rightPointer) // 2
            if self.prefixSumList[middlePointer] < targetValue:
                leftPointer = middlePointer + 1
            else:
                rightPointer = middlePointer
        return leftPointer
```
