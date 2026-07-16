# BFS Level Order Traversal

## python
```python
from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def level_order(root: Optional[TreeNode]) -> list[list[int]]:
    """Return node values grouped by level (BFS). O(n) time and space."""
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        level_size = len(queue)
        level = []
        for _ in range(level_size):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result


def level_order_flat(root: Optional[TreeNode]) -> list[int]:
    """Return all node values in BFS order (flat list)."""
    if not root:
        return []
    result, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        result.append(node.val)
        if node.left: queue.append(node.left)
        if node.right: queue.append(node.right)
    return result


# Build example tree:
#       3
#      / \
#     9  20
#       /  \
#      15   7
root = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
print(level_order(root))       # [[3], [9, 20], [15, 7]]
print(level_order_flat(root))  # [3, 9, 20, 15, 7]
```

## javascript
```javascript
function levelOrder(root) {
    if (!root) return [];
    const result = [], queue = [root];
    while (queue.length) {
        const level = [], size = queue.length;
        for (let i = 0; i < size; i++) {
            const node = queue.shift();
            level.push(node.val);
            if (node.left) queue.push(node.left);
            if (node.right) queue.push(node.right);
        }
        result.push(level);
    }
    return result;
}
```

## go
```go
func levelOrder(root *TreeNode) [][]int {
    if root == nil { return nil }
    var result [][]int
    queue := []*TreeNode{root}
    for len(queue) > 0 {
        size := len(queue)
        level := make([]int, size)
        for i := 0; i < size; i++ {
            node := queue[i]
            level[i] = node.Val
            if node.Left != nil { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        queue = queue[size:]
        result = append(result, level)
    }
    return result
}
```
