# Kth Lexicographical Path In Grid

<\!-- K-th Lexicographical Path in Grid Question Given a grid of size m x n, and the ability to move only right or down, find the k-th lexicographically sma -->

## python
```python
from math import comb

class Solution:
    def kthLexicographicalPath(self, m: int, n: int, k: int) -> str:
        """
        Returns the k-th lexicographically smallest path from (0,0) to (m-1,n-1).
        'H' means move right, 'V' means move down.
        """
        path = []
        totalH = n - 1
        totalV = m - 1
        while totalH > 0 or totalV > 0:
            if totalH == 0:
                path.append('V')
                totalV -= 1
            elif totalV == 0:
                path.append('H')
                totalH -= 1
            else:
                # How many paths if we take 'H' now?
                count = comb(totalH + totalV - 1, totalV)
                if k <= count:
                    path.append('H')
                    totalH -= 1
                else:
                    path.append('V')
                    k -= count
                    totalV -= 1
        return ''.join(path)
```
