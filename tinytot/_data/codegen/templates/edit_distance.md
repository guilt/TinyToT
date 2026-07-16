# Edit Distance

<\!-- Edit Distance Question Given two strings word1 and word2, return the minimum number of operations required to convert word1 to word2. You may perform  -->

## python
```python
class Solution:
    def minDistance(self, source: str, target: str) -> int:
        """
        Returns the minimum number of operations required to convert source to target using DP.
        """
        m, n = len(source), len(target)
        prev = list(range(n + 1))
        curr = [0] * (n + 1)
        for i in range(1, m + 1):
            curr[0] = i
            for j in range(1, n + 1):
                if source[i - 1] == target[j - 1]:
                    curr[j] = prev[j - 1]
                else:
                    curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
            prev, curr = curr, prev
        return prev[n]
```
