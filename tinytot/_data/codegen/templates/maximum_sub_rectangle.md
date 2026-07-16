# Maximum Sub Rectangle

<\!-- Maximum Sub Rectangle Sum Question Given a 2D matrix, find the sub-rectangle with the maximum sum. -->

## python
```python
from typing import List

class Solution:
    def maxSumRectangle(self, matrix: List[List[int]]) -> int:
        """
        Returns the maximum sum of any sub-rectangle in the given matrix.
        """
        if not matrix or not matrix[0]:
            return 0
        rows, cols = len(matrix), len(matrix[0])
        maxSum = float('-inf')
        for left in range(cols):
            rowSum = [0] * rows
            for right in range(left, cols):
                for i in range(rows):
                    rowSum[i] += matrix[i][right]
                # Apply Kadane's algorithm on rowSum
                maxSoFar = float('-inf')
                maxEndingHere = 0
                for value in rowSum:
                    maxEndingHere = max(value, maxEndingHere + value)
                    maxSoFar = max(maxSoFar, maxEndingHere)
                maxSum = max(maxSum, maxSoFar)
        return maxSum
```
