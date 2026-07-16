# B S T Sum Within L R

<\!-- BST Sum within L, R Question Find the sum of values of all nodes with value in the range [L, R] in a BST. -->

## python
```python
from typing import Optional

class TreeNode:
    val: int
    left: Optional['TreeNode'] = None
    right: Optional['TreeNode'] = None

class Solution:
    def rangeSumBST(self, root: TreeNode, low: int, high: int) -> int:
        if not root:
            return 0
        if root.val > high:
            return self.rangeSumBST(root.left, low, high)
        if root.val < low:
            return self.rangeSumBST(root.right, low, high)
        return root.val + self.rangeSumBST(root.left, low, high) + self.rangeSumBST(root.right, low, high)
```
