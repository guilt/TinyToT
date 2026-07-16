# B S T Two Sum

<\!-- BST Two Sum Problem Question Given the root of a binary search tree and a target value, determine if there exist two elements in the BST such that the -->

## python
```python
from typing import Optional

class TreeNode:
    def __init__(self, val: int, left: 'Optional[TreeNode]' = None, right: 'Optional[TreeNode]' = None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def findTarget(self, root: Optional[TreeNode], targetSum: int) -> bool:
        """
        Returns True if there exist two elements in the BST such that their sum is equal to targetSum.
        Uses explicit stack for in-order traversal and a set for complements.
        """
        if not root:
            return False
        nodeStack = []
        currentNode = root
        seenValues = set()
        while currentNode or nodeStack:
            while currentNode:
                nodeStack.append(currentNode)
                currentNode = currentNode.left
            currentNode = nodeStack.pop()
            if (targetSum - currentNode.val) in seenValues:
                return True
            seenValues.add(currentNode.val)
            currentNode = currentNode.right
        return False
```
