# Median Of Two Sorted Arrays

<\!-- Median of Two Sorted Arrays Question Find the median of two sorted arrays. -->

## python
```python
from typing import List

class Solution:
    def findMedianSortedArrays(self, numbersArrayA: List[int], numbersArrayB: List[int]) -> float:
        lengthOfArrayA, lengthOfArrayB = len(numbersArrayA), len(numbersArrayB)
        if lengthOfArrayA > lengthOfArrayB:
            numbersArrayA, numbersArrayB, lengthOfArrayA, lengthOfArrayB = numbersArrayB, numbersArrayA, lengthOfArrayB, lengthOfArrayA
        minPartitionIndex, maxPartitionIndex, halfLengthOfCombinedArray = 0, lengthOfArrayA, (lengthOfArrayA + lengthOfArrayB + 1) // 2
        while minPartitionIndex <= maxPartitionIndex:
            partitionIndexForArrayA = (minPartitionIndex + maxPartitionIndex) // 2
            partitionIndexForArrayB = halfLengthOfCombinedArray - partitionIndexForArrayA
            if partitionIndexForArrayA < lengthOfArrayA and numbersArrayB[partitionIndexForArrayB - 1] > numbersArrayA[partitionIndexForArrayA]:
                minPartitionIndex = partitionIndexForArrayA + 1
            elif partitionIndexForArrayA > 0 and numbersArrayA[partitionIndexForArrayA - 1] > numbersArrayB[partitionIndexForArrayB]:
                maxPartitionIndex = partitionIndexForArrayA - 1
            else:
                if partitionIndexForArrayA == 0:
                    maxOfLeftPartition = numbersArrayB[partitionIndexForArrayB - 1]
                elif partitionIndexForArrayB == 0:
                    maxOfLeftPartition = numbersArrayA[partitionIndexForArrayA - 1]
                else:
                    maxOfLeftPartition = max(numbersArrayA[partitionIndexForArrayA - 1], numbersArrayB[partitionIndexForArrayB - 1])
                if (lengthOfArrayA + lengthOfArrayB) % 2 == 1:
                    return maxOfLeftPartition
                if partitionIndexForArrayA == lengthOfArrayA:
                    minOfRightPartition = numbersArrayB[partitionIndexForArrayB]
                elif partitionIndexForArrayB == lengthOfArrayB:
                    minOfRightPartition = numbersArrayA[partitionIndexForArrayA]
                else:
                    minOfRightPartition = min(numbersArrayA[partitionIndexForArrayA], numbersArrayB[partitionIndexForArrayB])
                return (maxOfLeftPartition + minOfRightPartition) / 2.0
```
