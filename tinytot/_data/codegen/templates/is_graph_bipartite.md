# Is Graph Bipartite

<\!-- Is Graph Bipartite? Question Check if a graph is bipartite using coloring. -->

## python
```python
from typing import List

class Solution:
    def isBipartite(self, graph: List[List[int]]) -> bool:
        """
        Checks if a graph is bipartite using coloring.
        Returns True if bipartite, False otherwise.
        """
        nodeColor = {}
        for nodeIdx in range(len(graph)):
            if nodeIdx not in nodeColor:
                stack = [nodeIdx]
                nodeColor[nodeIdx] = 0
                while stack:
                    currNode = stack.pop()
                    for neighbor in graph[currNode]:
                        if neighbor not in nodeColor:
                            stack.append(neighbor)
                            nodeColor[neighbor] = nodeColor[currNode] ^ 1
                        elif nodeColor[neighbor] == nodeColor[currNode]:
                            return False
        return True
```
