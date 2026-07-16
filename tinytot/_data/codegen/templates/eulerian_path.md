# Eulerian Path

<\!-- Eulerian Path Question Given an undirected graph, determine if it contains an Eulerian Path or Cycle. An Eulerian Path visits every edge exactly once. -->

## python
```python
class Solution:
    def hasEulerianPath(self, graph: dict[int, list[int]]) -> bool:
        """
        Returns True if the undirected graph has an Eulerian Path.
        Eulerian Cycle: All vertices have even degree and the graph is connected.
        Eulerian Path: Exactly 0 or 2 vertices have odd degree and the graph is connected.
        """
        def dfs(node, visited):
            visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, visited)

        # Find a vertex with non-zero degree
        startNode = next((u for u in graph if graph[u]), None)
        if startNode is None:
            return False  # No edges

        visited = set()
        dfs(startNode, visited)
        # Check if all vertices with non-zero degree are connected
        for node in graph:
            if graph[node] and node not in visited:
                return False

        oddDegreeCount = sum(1 for node in graph if len(graph[node]) % 2 == 1)
        return oddDegreeCount == 0 or oddDegreeCount == 2
```
