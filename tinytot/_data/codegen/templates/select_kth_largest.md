# Select Kth Largest

<\!-- Select kth Largest Question Find the kth largest element in an array. -->

## python
```python
class Solution:
    def findKthLargest(self, nums: list[int], k: int) -> int:
        """
        Returns the kth largest element in an array.
        """

        def partition(leftIdx, rightIdx, pivotIdx):
            pivotVal = nums[pivotIdx]
            nums[pivotIdx], nums[rightIdx] = nums[rightIdx], nums[pivotIdx]
            storeIdx = leftIdx
            for i in range(leftIdx, rightIdx):
                if nums[i] < pivotVal:
                    nums[storeIdx], nums[i] = nums[i], nums[storeIdx]
                    storeIdx += 1
            nums[rightIdx], nums[storeIdx] = nums[storeIdx], nums[rightIdx]
            return storeIdx

        def select(leftIdx, rightIdx, kSmallest):
            if leftIdx == rightIdx:
                return nums[leftIdx]
            pivotIdx = random.randint(leftIdx, rightIdx)
            pivotIdx = partition(leftIdx, rightIdx, pivotIdx)
            if kSmallest == pivotIdx:
                return nums[kSmallest]
            elif kSmallest < pivotIdx:
                return select(leftIdx, pivotIdx - 1, kSmallest)
            else:
                return select(pivotIdx + 1, rightIdx, kSmallest)

        return select(0, len(nums) - 1, len(nums) - k)
```
