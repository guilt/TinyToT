# B S T Iterator Inorder Traversal

<\!-- BSTIterator Inorder Traversal Question Implement an iterator over a binary search tree (BST). Your iterator will be initialized with the root node of  -->

## python
```python
class BSTIterator:
    """
    Iterator over a binary search tree (BST).
    """
    def __init__(self, root: Optional[TreeNode]):
        self.nodeStack = []
        while root:
            self.nodeStack.append(root)
            root = root.left

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.nodeStack) <= 0:
            raise StopIteration

        node = self.nodeStack.pop()
        if node.right:
            tempRoot = node.right
            while tempRoot:
                self.nodeStack.append(tempRoot)
                tempRoot = tempRoot.left
        return node.val

class Solution:
    def iterate(self, root: Optional[TreeNode]):
        """
        Returns an iterator over the given binary search tree (BST).
        """
        return BSTIterator(root)
```
