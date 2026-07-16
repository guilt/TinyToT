# Subtree Of Another Tree

<\!-- Subtree of Another Tree Description Check if a given tree is a subtree of another tree. Example Input: root = [3,4,5,1,2], subRoot = [4,1,2] Output: t -->

## python
```python
from typing import Optional

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def isSubtree(self, root: Optional[TreeNode], subRoot: Optional[TreeNode]) -> bool:
        """
        Check if a given tree is a subtree of another tree.
        """
        if not root:
            return False
        if self.isSameTree(root, subRoot):
            return True
        return self.isSubtree(root.left, subRoot) or self.isSubtree(root.right, subRoot)

    def isSameTree(self, first: Optional[TreeNode], second: Optional[TreeNode]) -> bool:
        if not first and not second:
            return True
        if not first or not second:
            return False
        return first.val == second.val and self.isSameTree(first.left, second.left) and self.isSameTree(first.right, second.right)
```
