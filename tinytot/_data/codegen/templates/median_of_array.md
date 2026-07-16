# Median Of Array

<\!-- Median of an Array (QuickSelect) Question Find the median of an unsorted array using the QuickSelect algorithm. -->

## python
```python
import random
from typing import List

class Solution:
    def _quickSelect(self, arr: List[int], k: int) -> int:
        if len(arr) == 1:
            return arr[0]
        pivot = random.choice(arr)
        lows = [el for el in arr if el < pivot]
        highs = [el for el in arr if el > pivot]
        pivots = [el for el in arr if el == pivot]
        if k < len(lows):
            return self._quickSelect(lows, k)
        elif k < len(lows) + len(pivots):
            return pivots[0]
        else:
            return self._quickSelect(highs, k - len(lows) - len(pivots))

    def medianOfArray(self, arr: List[int]) -> float:
        """
            Find the median of an unsorted array using the QuickSelect algorithm.
        """
        n = len(arr)
        if n % 2 == 1:
            return float(self._quickSelect(arr, n // 2))
        else:
            return (self._quickSelect(arr, n // 2 - 1) + self._quickSelect(arr, n // 2)) / 2
```
