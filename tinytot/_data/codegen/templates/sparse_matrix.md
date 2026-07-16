# Sparse Matrix

<\!-- Implement a Sparse Matrix Question Implement a sparse matrix with efficient storage and iteration. -->

## python
```python
class Solution:

    class SparseVector:
        """
        Implements a sparse 1D vector using a dictionary to store non-zero values only.
        """
        def __init__(self):
            self.data = {}

        def set(self, idx: int, value: Any) -> None:
            """Sets the value at idx. Removes entry if value is zero."""
            if value != 0:
                self.data[idx] = value
            elif idx in self.data:
                del self.data[idx]

        def get(self, idx: int, defaultValue: Any = 0) -> Any:
            """Gets the value at idx, or 0 if not present."""
            return self.data.get(idx, defaultValue)

        def nonZeroPositions(self):
            """Returns a list of indices with non-zero values."""
            return self.data.keys()

    class SparseMatrix:
        """
        Implements a sparse matrix using a dictionary of SparseVector objects for rows.
        Only non-zero values are stored for efficiency.
        """
        __EMPTY_VECTOR = SparseVector()

        def __init__(self):
            self.data = {}

        def set(self, row: int, col: int, value: int) -> None:
            """Sets the value at (row, col). Removes entry if value is zero."""
            if value != 0:
                if row not in self.data:
                    self.data[row] = Solution.SparseVector()
                self.data[row].set(col, value)
            else:
                if row in self.data:
                    self.data[row].set(col, defaultValue)
                    if not self.data[row].data:
                        del self.data[row]

        def get(self, row: int, col: int, defaultValue: Any = 0) -> Any:
            """Gets the value at (row, col), or defaultValue if not present."""
            return self.data.get(row, Solution.SparseMatrix.__EMPTY_VECTOR).get(col, defaultValue)

        def nonZeroPositions(self):
            """Returns a list of (row, col) positions with non-zero values."""
            for row, sparseVector in self.data.items():
                for col in sparseVector.nonZeroPositions():
                    yield (row, col)
```
