# Leftmost Column With One

<\!-- Leftmost Column with a One Question Find the leftmost column with at least a one in a binary matrix. -->

## python
```python
from typing import List

class BinaryMatrix:
    def __init__(self, matrix: List[List[int]]):
        self.matrix = matrix

    def dimensions(self) -> List[int]:
        return [len(self.matrix), len(self.matrix[0])]

    def get(self, row: int, col: int) -> int:
        return self.matrix[row][col]

class Solution:
    def leftMostColumnWithOne(self, binaryMatrix: 'BinaryMatrix') -> int:
        """
        Returns the leftmost column with at least a one in a binary matrix.
        """
        numRows, numCols = binaryMatrix.dimensions()
        leftmost = float('inf')
        currCol = numCols - 1
        for rowIdx in range(numRows):
            while currCol >= 0 and binaryMatrix.get(rowIdx, currCol) == 1:
                leftmost = min(leftmost, currCol)
                currCol -= 1
            if currCol <= 0:
                break
        return leftmost if leftmost != float('inf') else -1
```
