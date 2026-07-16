# Perimeter Island

<\!-- Perimeter of Island Question LeetCode Here -->

## python
```python
from typing import List

class Solution:
    def islandPerimeter(self, grid: List[List[int]]) -> int:
        numRows = len(grid)
        numCols = len(grid[0])
        totalPerimeter = 0
        for rowIndex in range(numRows):
            for colIndex in range(numCols):
                if grid[rowIndex][colIndex]:
                    totalPerimeter += 4
                    if colIndex > 0 and grid[rowIndex][colIndex - 1]:
                        totalPerimeter -= 1
                    if rowIndex > 0 and grid[rowIndex - 1][colIndex]:
                        totalPerimeter -= 1
                    if rowIndex < (numRows - 1) and grid[rowIndex + 1][colIndex]:
                        totalPerimeter -= 1
                    if colIndex < (numCols - 1) and grid[rowIndex][colIndex + 1]:
                        totalPerimeter -= 1
        return totalPerimeter
```
