# Count Digit2s

<\!-- Count Digit ‘2’s in Numbers Question Count how many times the digit ‘2’ appears in all numbers from 0 to n (inclusive). Example Input: n = 25 Output:  -->

## python
```python
class Solution:
    def countDigit2s(self, n: int) -> int:
        """
        Returns the number of times digit '2' appears from 0 to n.
        """
        count = 0
        for i in range(n + 1):
            count += str(i).count('2')
        return count
```
