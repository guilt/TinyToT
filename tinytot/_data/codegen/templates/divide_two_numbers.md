# Divide Two Numbers

<\!-- Divide Two Numbers Question LeetCode Here -->

## python
```python
class Solution:
    def divide(self, dividend: int, divisor: int) -> int:
        """
        Returns the quotient of two integers.
        """
        isPositive = (dividend < 0) is (divisor < 0)
        absDividend, absDivisor = abs(dividend), abs(divisor)
        result = 0
        while absDividend >= absDivisor:
            temp, multiple = absDivisor, 1
            while absDividend >= temp:
                absDividend -= temp
                result += multiple
                multiple <<= 1
                temp <<= 1
        if not isPositive:
            result = -result
        return min(max(-2147483648, result), 2147483647)
```
