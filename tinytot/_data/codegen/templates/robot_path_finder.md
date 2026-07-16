# Robot Path Finder

<\!-- Robot Path Finder (MxN Grid) Question Given an MxN grid, find all paths from the top-left to the bottom-right corner. -->

## python
```python
from typing import List

class Solution:
    def robotPaths(self, m: int, n: int) -> List[List[tuple]]:
        """
        Returns a list of all possible paths from (1,1) to (m,n) in an m x n grid.
        Each path is represented as a list of (row, col) tuples.
        """
        resultPaths = []
        def backtrack(i, j, path):
            path.append((i, j))
            if i == m and j == n:
                resultPaths.append(path.copy())
            elif i > m or j > n:
                path.pop()
                return
            else:
                backtrack(i + 1, j, path)
                backtrack(i, j + 1, path)
            path.pop()
        backtrack(1, 1, [])
        return resultPaths
```
