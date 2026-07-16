# Toeplitz Matrix

<\!-- Toeplitz Matrix Question Check if a given matrix is a Toeplitz matrix. -->

## python
```python
class Solution:
    def isToeplitzMatrix(self, matrix: list[list[int]]) -> bool:
        """
        Returns True if the given matrix is a Toeplitz matrix.
        """
        rowIdx = 0
        while rowIdx + 1 < len(matrix):
            if matrix[rowIdx][:-1] != matrix[rowIdx + 1][1:]:
                return False
            rowIdx += 1
        return True
```
