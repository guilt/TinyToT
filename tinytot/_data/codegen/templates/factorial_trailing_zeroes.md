# Factorial Trailing Zeroes

<\!-- Factorial Trailing Zeroes Question Given a number n, count the number of trailing zeroes in n! (n factorial). -->

## python
```python
class Solution:
    def factorialTrailingZeroes(self, n: int) -> int:
        """
        Returns the number of trailing zeroes in n! by counting the number of times 5 divides numbers from 1 to n.
        """
        count = 0
        i = 5
        while n // i > 0:
            count += n // i
            i *= 5
        return count
```
