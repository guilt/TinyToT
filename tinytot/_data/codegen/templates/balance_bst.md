# Balance B S T

<\!-- BST - Convert and Rebalance Question Convert and rebalance a BST. -->

## python
```python
class TreeNode:
    val: int
    left: Optional['TreeNode'] = None
    right: Optional['TreeNode'] = None

class Solution:
    def balanceBst(self, root: TreeNode) -> TreeNode:
        """
        Returns the root of the balanced BST.
        """
        nodeList = []

        def inorder(node):
            if node:
                inorder(node.left)
                nodeList.append(node)
                inorder(node.right)

        def buildBalanced(left, right):
            if left <= right:
                midIndex = (left + right) // 2
                current = nodeList[midIndex]
                current.left = buildBalanced(left, midIndex - 1)
                current.right = buildBalanced(midIndex + 1, right)
                return current

        inorder(root)
        n = len(nodeList)
        return buildBalanced(0, n - 1)
```
