# Sudoku

<\!-- Sudoku Question Solve a standard 9x9 Sudoku puzzle using backtracking. -->

## python
```python
from typing import List

class Solution:
    def solveSudoku(self, board: str) -> str:
        """
        Solves the Sudoku puzzle in-place using a flat string and elegant helpers.
        """
        DIGITS = set('1', '2', '3', '4', '5', '6', '7', '8', '9')

        def sameRow(i: int, j: int) -> bool:
            return i // 9 == j // 9

        def sameCol(i: int, j: int) -> bool:
            return i % 9 == j % 9

        def sameBlock(i: int, j: int) -> bool:
            return (i // 27 == j // 27) and ((i % 9) // 3 == (j % 9) // 3)

        def recurse(board: str) -> str:
            i = board.find('0')
            if i == -1:
                return board
            excluded = set()
            for j in range(81):
                if sameRow(i, j) or sameCol(i, j) or sameBlock(i, j):
                    excluded.add(board[j])
            for m in DIGITS - excluded:
                result = recurse(board[:i] + m + board[i+1:])
                if result:
                    return result
            return ''

        return recurse(board)

if __name__ == '__main__':
    Solution().solveSudoku('0'*81) #0 is blank, L->R, T->B
```
