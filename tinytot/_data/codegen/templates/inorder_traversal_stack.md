# Inorder Traversal Stack

<\!-- Inorder Traversal Using Stack Question Given the root of a binary tree, return its inorder traversal using an explicit stack (not recursion). -->

## python
```python
from typing import Optional, List

class TreeNode:
    def __init__(self, val: int, left: 'Optional[TreeNode]' = None, right: 'Optional[TreeNode]' = None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def inorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        """
        Returns the inorder traversal of a binary tree using an explicit stack.
        """
        traversalResult = []
        nodeStack = []
        currentNode = root
        while currentNode or nodeStack:
            while currentNode:
                nodeStack.append(currentNode)
                currentNode = currentNode.left
            currentNode = nodeStack.pop()
            traversalResult.append(currentNode.val)
            currentNode = currentNode.right
        return traversalResult
```
