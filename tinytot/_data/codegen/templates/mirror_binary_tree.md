# Mirror Binary Tree

<\!-- Mirror a Binary Tree Question Given the root of a binary tree, mirror the tree (swap left and right children recursively). Example Input: 1 / \ 2 3 Ou -->

## python
```python
from typing import Optional

class TreeNode:
    def __init__(self, value: int, left: 'Optional[TreeNode]' = None, right: 'Optional[TreeNode]' = None):
        self.val = value
        self.left = left
        self.right = right

class Solution:
    def mirrorBinaryTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        if root is None:
            return None
        root.left, root.right = self.mirrorBinaryTree(root.right), self.mirrorBinaryTree(root.left)
        return root
```
