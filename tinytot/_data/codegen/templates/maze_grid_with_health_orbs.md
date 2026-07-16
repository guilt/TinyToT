# Maze Grid With Health Orbs

<\!-- Maze Grid with Health Orbs Question Given a grid where each cell contains a health orb (positive or negative value), find the maximum health achievabl -->

## python
```python
class Solution:
    def mazeWithHealth(self, grid: list[list[int]]) -> int:
        """
        Returns the maximum health achievable from top-left to bottom-right in the grid.
        Each cell may contain a health orb (positive) or demon (negative).
        """
        rows, cols = len(grid), len(grid[0])
        maxHealth = float('-inf')
        def dfs(x, y, health):
            nonlocal maxHealth
            if x == rows - 1 and y == cols - 1:
                maxHealth = max(maxHealth, health + grid[x][y])
                return
            for dx, dy in [(1, 0), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols:
                    dfs(nx, ny, health + grid[x][y])
        dfs(0, 0, 0)
        return maxHealth
```
