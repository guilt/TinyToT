# Topological Sort

<\!-- Topological Sort Question Given a directed acyclic graph (DAG), return a topological ordering of its nodes. -->

## python
```python
from typing import List, Dict

class Solution:
    def topologicalSort(self, graph: Dict[int, List[int]]) -> List[int]:
        """
        Returns a list of nodes in topological order for a DAG (Directed Acyclic Graph).
        Raises ValueError if the graph has a cycle.
        """
        visited = {}
        result = []
        def visit(node):
            if node in visited:
                if visited[node] == 1:
                    raise ValueError('Graph has a cycle!')
                return
            visited[node] = 1  # Temporary mark
            for neighbor in graph.get(node, []):
                visit(neighbor)
            visited[node] = 2  # Permanent mark
            result.append(node)
        for node in graph:
            if node not in visited:
                visit(node)
        result.reverse()
        return result
```
