# Math Calculator

<\!-- Math Calculator Question Implement a basic calculator to evaluate a simple expression string. -->

## python
```python
class Solution:
    def calculate(self, expr: str) -> int:
        """
        Returns the value of a simple expression string.
        """
        expr += '+'
        numStack = []
        currNum = 0
        prevOp = '+'
        for char in expr:
            if char.isdigit():
                currNum = currNum * 10 + int(char)
            elif char == ' ':
                continue
            else:
                if prevOp == '+':
                    numStack.append(currNum)
                elif prevOp == '-':
                    numStack.append(-currNum)
                elif prevOp == '*':
                    operand = numStack.pop()
                    numStack.append(operand * currNum)
                elif prevOp == '/':
                    operand = numStack.pop()
                    numStack.append(math.trunc(operand / currNum))
                currNum = 0
                prevOp = char
        return sum(numStack)
```
