# Insert Into Circular List

<\!-- Insert into Circular List Question Insert a value into a sorted circular linked list. -->

## python
```python
from typing import Optional

class Node:
    def __init__(self, val=None, next=None):
        self.val = val
        self.next = next

class Solution:
    def insert(self, head: Node, insertValue: int) -> Node:
        """
        Return the head of the circular linked list after inserting the value.
        """
        if not head:
            node = Node(insertValue)
            node.next = node
            return node
        previousNode, currentNode = head, head.next
        inserted = False
        while True:
            # Case 1: insertValue fits between two nodes in sorted order
            if previousNode.val <= insertValue <= currentNode.val:
                inserted = True
            # Case 2: at the rotation point (max to min), insertValue is new min or max
            elif previousNode.val > currentNode.val:
                if insertValue >= previousNode.val or insertValue <= currentNode.val:
                    inserted = True
            if inserted:
                previousNode.next = Node(insertValue, currentNode)
                return head
            previousNode, currentNode = currentNode, currentNode.next
            if previousNode == head:
                break
        # If not inserted in the loop, insert after last node (all values equal or single node)
        previousNode.next = Node(insertValue, currentNode)
        return head
```
