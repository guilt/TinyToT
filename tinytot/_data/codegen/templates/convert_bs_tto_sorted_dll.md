# Convert B S Tto Sorted D L L

<\!-- Convert BST to Sorted DLL Question Convert a binary search tree to a sorted doubly linked list in-place. -->

## python
```python
from typing import Optional

class Node:
    val: int
    left: Optional['Node'] = None
    right: Optional['Node'] = None

class Solution:
    def treeToDoublyList(self, root: Node) -> Node:
        """
        Converts a binary search tree to a sorted doubly linked list in-place.
        Returns the head of the sorted doubly linked list.
        """
        if not root:
            return None
        dummyNode = Node(-1)
        prevNode = dummyNode
        def inorder(currNode):
            nonlocal prevNode
            if not currNode:
                return
            inorder(currNode.left)
            prevNode.right, currNode.left, prevNode = currNode, prevNode, currNode
            inorder(currNode.right)
        inorder(root)
        dummyNode.right.left, prevNode.right = prevNode, dummyNode.right
        return dummyNode.right
```
