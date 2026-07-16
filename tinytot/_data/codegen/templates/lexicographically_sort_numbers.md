# Lexicographically Sort Numbers

<\!-- Lexicographically Sort Numbers Question Sort a given set of numbers lexicographically. Example Input: [1, 10, 2] Output: [1, 10, 2] -->

## python
```python
class Solution:
    def sortNumbers(self, nums: List[int]) -> List[int]:
        """
            Sort a given set of numbers lexicographically.
        """
        return sorted(nums, key=lambda x: str(x))
```
