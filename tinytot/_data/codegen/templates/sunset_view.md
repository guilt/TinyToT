# Sunset View

<\!-- Sunset View Question Given an array of building heights, return the number of buildings that can see the sunset (no taller building blocks the view to -->

## python
```python
class Solution:
    def sunsetView(self, heights: list[int]) -> int:
        """
        Returns the number of buildings that can see the sunset.
        """
        count = 0
        maxSoFar = float('-inf')
        for height in reversed(heights):
            if height > maxSoFar:
                count += 1
            maxSoFar = height
    return count
```
