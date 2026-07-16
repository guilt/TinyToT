# Trapping Rain Water

<\!-- Trapping Rain Water Question Given n non-negative integers representing an elevation map, compute how much water it can trap after raining. -->

## python
```python
from typing import List

class Solution:
    def trap(self, heights: List[int]) -> int:
        """
        Given n non-negative integers representing an elevation map, computes how much water it can trap after raining.
        Returns the total amount of trapped water.
        """
        leftMaxLevels = []
        leftMax = 0
        for h in heights:
            leftMax = max(leftMax, h)
            leftMaxLevels.append(leftMax)
        rightMax = 0
        for i, h in reversed(list(enumerate(heights))):
            rightMax = max(rightMax, h)
            leftMaxLevels[i] = min(leftMaxLevels[i], rightMax) - h
        return sum(leftMaxLevels)
```
