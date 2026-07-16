# Right Sided View

<\!-- Right Sided View (Max of Level’s Right) Question Return the values of the nodes you can see ordered from top to bottom when looking at a binary tree f -->

## python
```python
class Solution:
    def rightSideView(self, root):
        """
        Returns the values of the nodes you can see ordered from top to bottom when looking at a binary tree from the right side.
        """
        levelValues = {}
        def dfs(node, height):
            if not node:
                return
            dfs(node.right, height + 1)
            if height not in levelValues:
                levelValues[height] = node.val
            dfs(node.left, height + 1)
        dfs(root, 0)
        return [levelValues[i] for i in range(len(levelValues))]
```
