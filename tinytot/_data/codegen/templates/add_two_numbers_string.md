# Add Two Numbers String

<\!-- Add Two Numbers Mathematically Question Given two non-negative integers num1 and num2 represented as string, return the sum as a string. -->

## python
```python
class Solution:
    def addStrings(self, firstNumStr: str, secondNumStr: str) -> str:
        """
        Returns the sum of two non-negative integers represented as strings.
        """

        firstNumStr = firstNumStr[::-1]
        secondNumStr = secondNumStr[::-1]

        if len(firstNumStr) < len(secondNumStr):
            firstNumStr += '0' * (len(secondNumStr) - len(firstNumStr))
        else:
            secondNumStr += '0' * (len(firstNumStr) - len(secondNumStr))

        carryOver = 0
        resultString = ''

        for charIndex in range(len(firstNumStr)):
            digitSum = int(firstNumStr[charIndex]) + int(secondNumStr[charIndex]) + carryOver
            carryOver = digitSum // 10
            resultString += str(digitSum % 10)
        if carryOver > 0:
            resultString += str(carryOver)

        return resultString[::-1]
```
