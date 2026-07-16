# Can Place Flowers

<\!-- Can Place Flowers Question Given a flowerbed (represented as an array of 0s and 1s), where 0 represents an empty plot and 1 represents a flower, deter -->

## python
```python
from typing import List

class Solution:
    def canPlaceFlowers(self, flowerbed: List[int], n: int) -> bool:
        """
        Determine if a given number of new flowers can be planted in the flowerbed without violating the no-adjacent-flowers rule.
        """
        if n == 0:
            return True

        for i in range(len(flowerbed)):
            if flowerbed[i] == 0 and (i == 0 or flowerbed[i-1] == 0) and (i == len(flowerbed)-1 or flowerbed[i+1] == 0):
                flowerbed[i] = 1
                n -= 1
                if n == 0:
                    return True

        return False
```
