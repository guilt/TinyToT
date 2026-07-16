# Binary Tree All Paths

<\!-- Binary Tree All Paths Problem Statement Given a binary tree, return all root-to-leaf paths. -->

## python
```python
from typing import List, Optional

class Solution:
    def binaryTreePaths(self, root: Optional[TreeNode]) -> List[str]:
        """
        Return all root-to-leaf paths in a binary tree.
        """
        if not root:
            return []

        paths = []

        def dfs(node, path):
            if not node.left and not node.right:
                paths.append(path + str(node.val))
                return

            if node.left:
                dfs(node.left, path + str(node.val) + '->')
            if node.right:
                dfs(node.right, path + str(node.val) + '->')

        dfs(root, '')
        return paths
```
