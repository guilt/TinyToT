# Fish And Bait

<\!-- Fish and Bait Question Imagine that you are going fishing at the local pond. The size of the bait must be strictly smaller than the size of the fish f -->

## python
```python
class Solution:
    def maxFish(self, fish: List[int], bait: List[int], N: int) -> int:
        """
        Find the maximum number of fish that can be caught with a given amount of bait, assuming a bait can be reused N times.
        """
        fish.sort()
        bait.sort()

        i = 0
        j = 0

        count = 0
        n = 0

        while i < len(fish) and j < len(bait):
            if fish[i] <= bait[j]:
                i += 1
                count += 1
                n += 1
                if n == N:
                    j += 1
                    n = 0
            else:
                j += 1
                n = 0

        return count
```
