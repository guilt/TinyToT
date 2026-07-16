# Closest Value In B S T

<\!-- Closest Value in BST Question Find the value in a BST that is closest to the given target. -->

## python
```python
class Solution:
    def closestValue(self, root: TreeNode, targetValue: float) -> int:
        closest = root.val
        currentNode = root
        while currentNode:
            if abs(currentNode.val - targetValue) < abs(closest - targetValue):
                closest = currentNode.val
            if targetValue < currentNode.val:
                currentNode = currentNode.left
            else:
                currentNode = currentNode.right
        return closest
```
