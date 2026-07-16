# Queue

## python
```python
from collections import deque


class Queue:
    """FIFO queue backed by collections.deque (O(1) enqueue and dequeue)."""

    def __init__(self) -> None:
        self._items: deque = deque()

    def enqueue(self, item) -> None:
        """Add item to the back of the queue."""
        self._items.append(item)

    def dequeue(self):
        """Remove and return the front item. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        return self._items.popleft()

    def front(self):
        """Return the front item without removing it."""
        if self.is_empty():
            raise IndexError("peek at empty queue")
        return self._items[0]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self) -> int:
        return len(self._items)


# Example
q = Queue()
q.enqueue(1); q.enqueue(2); q.enqueue(3)
print(q.dequeue())  # 1
print(q.front())    # 2
```
