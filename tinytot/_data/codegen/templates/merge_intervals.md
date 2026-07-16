# Merge Intervals

<\!-- Merge Intervals Question Merge all overlapping intervals. -->

## python
```python
from typing import List

class Solution:
    def merge(self, intervalList: List[List[int]]) -> List[List[int]]:
        """
        Merges all overlapping intervals in the input list.
        Returns a list of merged intervals.
        """
        intervalList.sort(key=lambda interval: interval[0])
        mergedIntervals = []
        for interval in intervalList:
            if not mergedIntervals or mergedIntervals[-1][1] < interval[0]:
                mergedIntervals.append(interval)
            else:
                mergedIntervals[-1][1] = max(mergedIntervals[-1][1], interval[1])
        return mergedIntervals
```
