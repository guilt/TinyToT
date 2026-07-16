# Interval List Intersections

<\!-- Interval List Intersections Question Given two lists of closed intervals, each list of intervals is pairwise disjoint and in sorted order. Find the in -->

## python
```python
from typing import List

class Solution:
    def intervalIntersection(self, firstIntervalList: List[List[int]], secondIntervalList: List[List[int]]) -> List[List[int]]:
        """
        Returns the intersection of two lists of intervals.
        """
        firstPointer = 0
        secondPointer = 0
        totalFirstIntervals = len(firstIntervalList)
        totalSecondIntervals = len(secondIntervalList)
        intersectionList = []
        while firstPointer < totalFirstIntervals and secondPointer < totalSecondIntervals:
            currentFirstInterval = firstIntervalList[firstPointer]
            currentSecondInterval = secondIntervalList[secondPointer]
            lowerBound = max(currentFirstInterval[0], currentSecondInterval[0])
            upperBound = min(currentFirstInterval[1], currentSecondInterval[1])
            if lowerBound <= upperBound:
                intersectionList.append([lowerBound, upperBound])
            if currentFirstInterval[1] < currentSecondInterval[1]:
                firstPointer += 1
            else:
                secondPointer += 1
        return intersectionList
```
