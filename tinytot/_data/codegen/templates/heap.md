# Heap

## python
```python
import heapq

# Python's heapq module implements a min heap
heap = []
for v in [3, 1, 4, 1, 5, 9, 2, 6]:
    heapq.heappush(heap, v)

print(heapq.heappop(heap))  # 1 (smallest)
print(heapq.heappop(heap))  # 1

# heapify an existing list in-place: O(n)
data = [3, 1, 4, 1, 5, 9]
heapq.heapify(data)

# k smallest / largest
print(heapq.nsmallest(3, data))   # [1, 1, 3]
print(heapq.nlargest(3, data))    # [9, 5, 4]
```

### Max heap variant

```python
import heapq


class MaxHeap:
    """Max heap using Python's heapq (which is a min heap) with negation."""

    def __init__(self):
        self._heap = []

    def push(self, value):
        heapq.heappush(self._heap, -value)

    def pop(self) -> int:
        return -heapq.heappop(self._heap)

    def peek(self) -> int:
        return -self._heap[0]

    def __len__(self):
        return len(self._heap)


# Or use the standard library directly:
# import heapq
# heap = []
# heapq.heappush(heap, value)      # min heap
# smallest = heapq.heappop(heap)
# heapq.nlargest(k, iterable)      # k largest elements

h = MaxHeap()
for v in [3, 1, 4, 1, 5, 9]:
    h.push(v)
print(h.pop())   # 9
print(h.peek())  # 5
```
