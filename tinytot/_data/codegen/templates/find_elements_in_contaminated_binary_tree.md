# Find Elements In Contaminated Binary Tree

<\!-- Find Elements in a Contaminated Binary Tree Given a binary tree with the following rules: root.val == 0 For any treeNode: If treeNode.val == x and tre -->

## python
```python
class FindElements:
    def __init__(self, root):
        self.recoveredValues = set()
        root.val = 0
        self._recoverTree(root)

    def _recoverTree(self, root):
        if not root:
            return
        self.recoveredValues.add(root.val)
        if root.left:
            root.left.val = 2 * root.val + 1
            self._recoverTree(root.left)
        if root.right:
            root.right.val = 2 * root.val + 2
            self._recoverTree(root.right)

class Solution:

    def find(self, root, target):
        """
        Returns true if the target value exists in the recovered binary tree.
        """
        foundElements = FindElements(root)
        return target in foundElements.recoveredValues
```
