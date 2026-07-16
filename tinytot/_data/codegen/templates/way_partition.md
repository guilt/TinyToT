# Way Partition

<\!-- 3 Way Partition Question Partition an array into three parts: elements less than a pivot, equal to the pivot, and greater than the pivot. -->

## python
```python
class Solution:

    def threeWayPartition(self, arr: List[int], pivot: int) -> None:
        """
        Partitions the array into three parts: elements less than pivot, equal to pivot, and greater than pivot.
        """
        low = 0
        mid = 0
        high = len(arr) - 1
        while mid <= high:
            if arr[mid] < pivot:
                arr[low], arr[mid] = arr[mid], arr[low]
                low += 1
                mid += 1
            elif arr[mid] == pivot:
                mid += 1
            else:
                arr[mid], arr[high] = arr[high], arr[mid]
                high -= 1
```
