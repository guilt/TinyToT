# Remove Nth From End Of Linked List

<\!-- Remove Nth Element from End of Linked List Question Remove the nth node from the end of a linked list and return its head. -->

## python
```python
from typing import Optional

class ListNode:
    def __init__(self, val: int = 0, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next

class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], nFromEnd: int) -> Optional[ListNode]:
        """
        Removes the nth node from the end of a linked list and returns its head.
        """
        dummyNode = ListNode(0)
        dummyNode.next = head
        firstPointer = dummyNode
        secondPointer = dummyNode
        for _ in range(nFromEnd + 1):
            firstPointer = firstPointer.next
        while firstPointer:
            firstPointer = firstPointer.next
            secondPointer = secondPointer.next
        secondPointer.next = secondPointer.next.next
        return dummyNode.next
```
