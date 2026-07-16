# Add Binary Numbers

<\!-- Add Binary Numbers Question Add two binary numbers represented as strings. -->

## python
```python
class Solution:
    def addBinary(self, binA: str, binB: str) -> str:
        """
        Returns the sum of two binary numbers represented as strings.
        """
        carry = 0
        result = ''
        stackA = list(binA)
        stackB = list(binB)
        while stackA or stackB or carry:
            if stackA:
                carry += int(stackA.pop())
            if stackB:
                carry += int(stackB.pop())
            result += str(carry % 2)
            carry //= 2
        return result[::-1]
```
