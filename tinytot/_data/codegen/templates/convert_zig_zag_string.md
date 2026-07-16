# Convert Zig Zag String

<\!-- Convert ZigZag String Question Convert a string to a zigzag pattern on a given number of rows. -->

## python
```python
class Solution:
    def convert(self, inputString: str, numRows: int) -> str:
        if numRows == 1 or numRows >= len(inputString):
            return inputString
        rowStrings = [''] * numRows
        currentRow = 0
        direction = 1
        for char in inputString:
            rowStrings[currentRow] += char
            if currentRow == 0:
                direction = 1
            elif currentRow == numRows - 1:
                direction = -1
            currentRow += direction
        return ''.join(rowStrings)
```
