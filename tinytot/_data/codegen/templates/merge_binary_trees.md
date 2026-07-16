# Merge Binary Trees

<\!-- Merge Binary Trees Question You are given two binary trees root1 and root2 . Imagine that when you put one of them to cover the other, some nodes of t -->

## python
```python
from typing import Optional

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def mergeTrees(self, root1: Optional[TreeNode], root2: Optional[TreeNode]) -> Optional[TreeNode]:
        """
        Merge two binary trees into a new binary tree.
        """
        if not root1 and not root2:
            return None

        if not root1:
            return root2

        if not root2:
            return root1

        newRoot = TreeNode(root1.val + root2.val)
        newRoot.left = self.mergeTrees(root1.left, root2.left)
        newRoot.right = self.mergeTrees(root1.right, root2.right)

        return newRoot
```
