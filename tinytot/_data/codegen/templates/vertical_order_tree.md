# Vertical Order Tree

<\!-- Vertical Order of a Tree Question Return the vertical order traversal of a binary tree’s nodes’ values. -->

## python
```python
import collections

class Solution:
    def verticalOrder(self, root):
        """
        Returns the vertical order traversal of a binary tree's nodes' values.
        Each vertical level is grouped together in the result.
        """
        colMap = collections.defaultdict(list)
        nodeQueue = [(root, 0)]
        for node, colIdx in nodeQueue:
            if node:
                colMap[colIdx].append(node.val)
                nodeQueue += (node.left, colIdx - 1), (node.right, colIdx + 1)
        return [colMap[i] for i in sorted(colMap)]
```
