# K Distance Nodes

<\!-- K Distance Nodes Question Return all nodes at distance K from the target node in a binary tree. -->

## python
```python
import collections

class Solution:
    def distanceK(self, root: TreeNode, targetNode: TreeNode, kDistance: int) -> List[int]:
        adjacencyList = collections.defaultdict(list)

        def buildGraph(currentNode, parentNode):
            if currentNode:
                if parentNode:
                    adjacencyList[currentNode.val].append(parentNode.val)
                    adjacencyList[parentNode.val].append(currentNode.val)
                buildGraph(currentNode.left, currentNode)
                buildGraph(currentNode.right, currentNode)
        buildGraph(root, None)
        queue = collections.deque([(targetNode.val, 0)])
        visited = {targetNode.val}
        nodesAtDistanceK = []
        while queue:
            nodeVal, currentDistance = queue.popleft()
            if currentDistance == kDistance:
                nodesAtDistanceK.append(nodeVal)
            for neighbor in adjacencyList[nodeVal]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, currentDistance + 1))
        return nodesAtDistanceK
```
