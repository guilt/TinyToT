# Egg Drop Problem

<\!-- Egg Drop Problem Question Given eggs and floors , find the minimum number of attempts needed in the worst case to determine the highest floor from whi -->

## python
```python
class Solution:
    def eggDrop(self, eggs: int, floors: int) -> int:
        """
        Returns the minimum number of attempts needed in the worst case to find the critical floor.
        """
        dp = [[0] * (floors + 1) for _ in range(eggs + 1)]
        for i in range(1, eggs + 1):
            for j in range(1, floors + 1):
                if i == 1:
                    dp[i][j] = j
                elif j == 1:
                    dp[i][j] = 1
                else:
                    dp[i][j] = min(1 + max(dp[i - 1][x - 1], dp[i][j - x]) for x in range(1, j + 1))
        return dp[eggs][floors]
```
