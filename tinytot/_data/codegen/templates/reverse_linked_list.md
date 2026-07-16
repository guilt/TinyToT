# Reverse Linked List

<\!-- Reverse Linked List Question Reverse a singly linked list. -->

## python
```python
from typing import Optional

class ListNode:
    def __init__(self, val: int = 0, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next

class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """
        Reverses a singly linked list.
        Returns the new head of the reversed list.
        """
        previousNode = None
        currentNode = head
        while currentNode:
            nextNode = currentNode.next
            currentNode.next = previousNode
            previousNode = currentNode
            currentNode = nextNode
        return previousNode
```
