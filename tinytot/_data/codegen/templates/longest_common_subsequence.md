# Longest Common Subsequence

<\!-- Longest Common Subsequence Question Given two sequences, find the length of their longest common subsequence. -->

## python
```python
from typing import List

class Solution:
    def longestCommonSubsequence(self, firstSequence: List, secondSequence: List) -> int:
        """
        Returns the length of the longest common subsequence between two lists.
        Uses a simplified and more readable dynamic programming approach.
        """
        numRows, numCols = len(firstSequence), len(secondSequence)
        dp = [0] * (numCols + 1)
        for rowIdx in range(1, numRows + 1):
            previousDiagonal = 0
            for colIdx in range(1, numCols + 1):
                temp = dp[colIdx]
                if firstSequence[rowIdx - 1] == secondSequence[colIdx - 1]:
                    dp[colIdx] = previousDiagonal + 1
                else:
                    dp[colIdx] = max(dp[colIdx], dp[colIdx - 1])
                previousDiagonal = temp
        return dp[numCols]
```
