# Hierholzers Algorithm

<\!-- Hierholzer’s Algorithm (Eulerian Circuit/Path Construction) Question Given an undirected graph, construct an Eulerian circuit or path (if it exists) u -->

## python
```python
class Solution:
    def findEulerianPath(self, graph: dict[int, list[int]]) -> list[int]:
        """
        Returns a list of vertices representing the Eulerian path or circuit in the graph.
        If no Eulerian path exists, returns an empty list.
        The graph is represented as an adjacency list (dict of lists).
        """
        import copy
        g = copy.deepcopy(graph)
        # Find the start node: odd degree if exists, else any node with edges
        odd = [u for u in g if len(g[u]) % 2 == 1]
        if len(odd) == 0:
            start = next((u for u in g if g[u]), None)
        elif len(odd) == 2:
            start = odd[0]
        else:
            return []  # No Eulerian path
        stack = [start]
        path = []
        while stack:
            node = stack[-1]
            if g[node]:
                neighbor = g[node].pop()
                g[neighbor].remove(node)
                stack.append(neighbor)
            else:
                path.append(stack.pop())
        return path[::-1]  # Path is constructed in reverse
```
