# Linked List Cycle

<\!-- Linked List Cycle Question Check if a linked list has a cycle. -->

## python
```python
from typing import Optional

class ListNode:
    def __init__(self, val: int = 0, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next

class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        """
        Checks if a linked list has a cycle.
        Returns True if a cycle exists, False otherwise.
        """
        slow = head
        fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow == fast:
                return True
        return False
```
