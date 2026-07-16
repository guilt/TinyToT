# Minimum Pushes Box

<\!-- Minimum Pushes Box Question Find the minimum number of pushes required to move a box to a target location in a grid. -->

## python
```python
import heapq
from typing import List, Set, Tuple

class Solution:
    def minPushBox(self, grid: List[List[str]]) -> int:
        """
        Find the minimum number of pushes required to move a box to a target location in a grid.
        """
        playerPos = boxPos = targetPos = None
        freeCells: Set[Tuple[int, int]] = set()
        for rowIdx, row in enumerate(grid):
            for colIdx, cell in enumerate(row):
                if cell == '#':
                    continue
                if cell == 'S':
                    playerPos = (rowIdx, colIdx)
                if cell == 'B':
                    boxPos = (rowIdx, colIdx)
                if cell == 'T':
                    targetPos = (rowIdx, colIdx)
                freeCells.add((rowIdx, colIdx))
        heap = [(0, *playerPos, *boxPos)]
        visitedStates = set()
        while heap:
            numPushes, playerRow, playerCol, boxRow, boxCol = heapq.heappop(heap)
            if (boxRow, boxCol) == targetPos:
                return numPushes
            if (playerRow, playerCol, boxRow, boxCol) in visitedStates:
                continue
            visitedStates.add((playerRow, playerCol, boxRow, boxCol))
            for dRow, dCol in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nextPlayerRow, nextPlayerCol = playerRow + dRow, playerCol + dCol
                nextBoxRow, nextBoxCol = boxRow + dRow, boxCol + dCol
                if (nextPlayerRow, nextPlayerCol) == (boxRow, boxCol) and (nextBoxRow, nextBoxCol) in freeCells:
                    heapq.heappush(heap, (numPushes + 1, nextPlayerRow, nextPlayerCol, nextBoxRow, nextBoxCol))
                elif (nextPlayerRow, nextPlayerCol) in freeCells and (nextPlayerRow, nextPlayerCol) != (boxRow, boxCol):
                    heapq.heappush(heap, (numPushes, nextPlayerRow, nextPlayerCol, boxRow, boxCol))
        return -1
```
