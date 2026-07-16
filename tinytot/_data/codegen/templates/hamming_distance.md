# Hamming Distance

<\!-- Hamming Distance Question Given two integers, compute the number of positions at which the corresponding bits are different. -->

## python
```python
class Solution:
    def hammingDistance(self, firstNumber: int, secondNumber: int) -> int:
        """
        Returns the Hamming distance between two integers.
        """
        xorResult = firstNumber ^ secondNumber
        distance = 0
        while xorResult:
            distance += xorResult & 1
            xorResult >>= 1
        return distance
```
