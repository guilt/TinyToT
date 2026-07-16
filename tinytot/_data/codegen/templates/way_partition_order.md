# Way Partition Order

<\!-- 3 Way Partition Order Description Partition an array into three parts: elements less than a pivot, equal to the pivot, and greater than the pivot, whi -->

## python
```python
class Solution:
    def threeWayPartitionWithRelativeOrder(self, arr, pivot):
        less = 0
        equal = 0
        greater = len(arr) - 1

        while equal <= greater:
            if arr[equal] < pivot:
                arr[less], arr[equal] = arr[equal], arr[less]
                less += 1
                equal += 1
            elif arr[equal] == pivot:
                equal += 1
            else:
                arr[equal], arr[greater] = arr[greater], arr[equal]
                greater -= 1

        return arr
```
