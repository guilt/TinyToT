# Bst

## python
```python
class BSTNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None


class BinarySearchTree:
    """Binary Search Tree: left < node <= right."""

    def __init__(self):
        self.root: BSTNode | None = None

    def insert(self, value) -> None:
        self.root = self._insert(self.root, value)

    def _insert(self, node, value):
        if node is None:
            return BSTNode(value)
        if value < node.value:
            node.left = self._insert(node.left, value)
        elif value > node.value:
            node.right = self._insert(node.right, value)
        return node

    def search(self, value) -> bool:
        return self._search(self.root, value)

    def _search(self, node, value) -> bool:
        if node is None:
            return False
        if value == node.value:
            return True
        if value < node.value:
            return self._search(node.left, value)
        return self._search(node.right, value)

    def inorder(self) -> list:
        """Return elements in sorted order."""
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append(node.value)
            self._inorder(node.right, result)


# Example
bst = BinarySearchTree()
for v in [5, 3, 7, 1, 4, 6, 8]:
    bst.insert(v)
print(bst.inorder())      # [1, 3, 4, 5, 6, 7, 8]
print(bst.search(4))      # True
print(bst.search(9))      # False
```
