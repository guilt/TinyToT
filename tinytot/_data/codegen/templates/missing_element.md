# Missing Element

<\!-- Missing Element Question Find the k-th missing element in a sorted array. -->

## python
```python
class Solution:
    def findKthMissingElement(self, sortedArray: List[int], targetMissingCount: int) -> int:
        arrayLength = len(sortedArray)
        for arrayIndex in range(arrayLength - 1):
            missingElementsBetween = sortedArray[arrayIndex + 1] - sortedArray[arrayIndex] - 1
            if targetMissingCount <= missingElementsBetween:
                return sortedArray[arrayIndex] + targetMissingCount
            targetMissingCount -= missingElementsBetween
        return sortedArray[-1] + targetMissingCount
        return nums[left - 1] + k - missing(left - 1)
```
