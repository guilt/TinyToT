# k Sorted Points

<\!-- k Sorted Points Question Given a list of points on a plane, find the k closest points to the origin (0, 0). -->

## python
```python
from typing import List

class Solution:
    def kClosest(self, pointList: List[List[int]], kClosest: int) -> List[List[int]]:
        """
        Returns the k closest points to the origin (0, 0).
        """
        def squaredDistance(point: List[int]) -> int:
            xCoord, yCoord = point[0], point[1]
            return xCoord ** 2 + yCoord ** 2
        sortedPoints = sorted(pointList, key=squaredDistance)
        return sortedPoints[:kClosest]
```
