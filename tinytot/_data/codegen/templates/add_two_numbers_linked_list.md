# Add Two Numbers Linked List

<\!-- Add Two Numbers (Linked List) Question Add two numbers represented by linked lists. -->

## python
```python
from typing import Optional

class ListNode:
    def __init__(self, val: int = 0, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, firstListNode: Optional[ListNode], secondListNode: Optional[ListNode]) -> Optional[ListNode]:
        """
        Adds two numbers represented by linked lists and returns the sum as a linked list.
        Each node contains a single digit. The digits are stored in reverse order.
        """
        dummyHeadNode = ListNode()
        currentResultNode = dummyHeadNode
        carryOver = 0
        while firstListNode or secondListNode:
            currentSum = carryOver
            if firstListNode:
                currentSum += firstListNode.val
            if secondListNode:
                currentSum += secondListNode.val
            carryOver = currentSum // 10
            currentSum = currentSum % 10
            currentResultNode.next = ListNode(currentSum)
            currentResultNode = currentResultNode.next
            firstListNode = firstListNode.next if firstListNode else None
            secondListNode = secondListNode.next if secondListNode else None
        if carryOver != 0:
            currentResultNode.next = ListNode(carryOver)
        return dummyHeadNode.next
```
