# Shortest Distance From All Buildings

<\!-- Shortest Distance from All Buildings Question Find the shortest distance from all buildings. -->

## python
```python
import collections

def shortestDistanceFromAllBuildings(grid):
    """
    Return the shortest distance from all buildings.
    """
    if not grid or not grid[0]:
        return -1
    numRows = len(grid)
    numCols = len(grid[0])
    totalBuildings = sum(cell for row in grid for cell in row if cell == 1)
    reachCount = [[0] * numCols for _ in range(numRows)]
    distanceSum = [[0] * numCols for _ in range(numRows)]

    def bfs(buildingRow, buildingCol):
        visited = [[False] * numCols for _ in range(numRows)]
        visited[buildingRow][buildingCol] = True
        queue = collections.deque([(buildingRow, buildingCol, 0)])
        buildingsReached = 1
        while queue:
            row, col, dist = queue.popleft()
            for nextRow, nextCol in (
                (row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)
            ):
                if (
                    0 <= nextRow < numRows and 0 <= nextCol < numCols
                    and not visited[nextRow][nextCol]
                ):
                    visited[nextRow][nextCol] = True
                    if grid[nextRow][nextCol] == 0:
                        queue.append((nextRow, nextCol, dist + 1))
                        reachCount[nextRow][nextCol] += 1
                        distanceSum[nextRow][nextCol] += dist + 1
                    elif grid[nextRow][nextCol] == 1:
                        buildingsReached += 1
        return buildingsReached == totalBuildings

    for row in range(numRows):
        for col in range(numCols):
            if grid[row][col] == 1:
                if not bfs(row, col):
                    return -1
    minDistance = min(
        [
            distanceSum[r][c]
            for r in range(numRows)
            for c in range(numCols)
            if grid[r][c] == 0 and reachCount[r][c] == totalBuildings
        ]
        or [-1]
    )
    return minDistance
```
