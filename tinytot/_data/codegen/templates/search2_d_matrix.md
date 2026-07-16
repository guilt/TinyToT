# Search2 D Matrix

<\!-- Search a 2D Matrix Question Search for a value in an m x n matrix with sorted rows and columns. Examples Input: matrix = [[1, 4, 7, 11, 15], [2, 5, 8, -->

## python
```python
def searchMatrix(matrix, target):
    if not matrix or not matrix[0]:
        return False

    rows, cols = len(matrix), len(matrix[0])
    left, right = 0, rows * cols - 1

    while left <= right:
        mid = (left + right) // 2
        midValue = matrix[mid // cols][mid % cols]

        if midValue == target:
            return True
        elif midValue < target:
            left = mid + 1
        else:
            right = mid - 1

    return False
```
