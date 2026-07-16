# L L R B

<\!-- Left-Leaning Red-Black Tree (LLRB) Question Implement a left-leaning red-black tree (LLRB) with basic insertion and search operations in Python. Examp -->

## python
```python
from enum import Enum

class Color(Enum):
    RED = 1
    BLACK = 0

    def other(self) -> 'Color':
        return Color.BLACK if self == Color.RED else Color.RED

class Node:
    def __init__(self, key: int, value, color: Color):
        self.key = key
        self.value = value
        self.color = color  # Color.RED or Color.BLACK
        self.left = None
        self.right = None

class LeftLeaningRedBlackTree:
    """
    Returns the root of the left-leaning red-black tree.
    """
    def __init__(self):
        self.root = None

    def insert(self, key: int, value=None) -> None:
        self.root = self._insert(self.root, key, value)
        self.root.color = Color.BLACK

    def get(self, key: int):
        node = self.root
        while node is not None:
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else:
                return node.value
        return None

    def __iter__(self):
        """In-order traversal yielding keys in sorted order."""
        stack, node = [], self.root
        while stack or node:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            yield node.key
            node = node.right

    #  Private helpers below
    def _isRed(self, node) -> bool:
        return node is not None and node.color == Color.RED

    def _rotateLeft(self, h):
        x = h.right
        h.right = x.left
        x.left = h
        x.color = h.color
        h.color = Color.RED
        return x

    def _rotateRight(self, h):
        x = h.left
        h.left = x.right
        x.right = h
        x.color = h.color
        h.color = Color.RED
        return x

    def _flipColors(self, h):
        h.color = h.color.other()
        if h.left:
            h.left.color = h.left.color.other()
        if h.right:
            h.right.color = h.right.color.other()

    def _insert(self, h, key, value):
        if h is None:
            return Node(key, value, Color.RED)
        if key < h.key:
            h.left = self._insert(h.left, key, value)
        elif key > h.key:
            h.right = self._insert(h.right, key, value)
        else:
            raise ValueError(f"Duplicate key insertion attempted: {key}")

        if self._isRed(h.right) and not self._isRed(h.left):
            h = self._rotateLeft(h)
        if self._isRed(h.left) and self._isRed(h.left.left):
            h = self._rotateRight(h)
        if self._isRed(h.left) and self._isRed(h.right):
            self._flipColors(h)
        return h

class Solution:
    def sortNumbers(self, nums: list[int]) -> list[int]:
        """Sorts a list of numbers using a Left-Leaning Red-Black Tree."""
        tree = LeftLeaningRedBlackTree()
        for num in nums:
            tree.insert(num)
        return list(tree)
```
