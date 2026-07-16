# Graph Valid Tree

<\!-- Graph Valid Tree You have a graph of n nodes labeled from 0 to n - 1. You are given an integer n and a list of edges where edges[i] = [ai, bi] indicat -->

## python
```python
from typing import List
from collections import defaultdict

class Solution:
    def validTree(self, n: int, edges: List[List[int]]) -> bool:
        """
            Return true if the edges of the given graph make up a valid tree, and false otherwise.
        """
        if len(edges) != n - 1:
            return False

        graph = defaultdict(list)
        for u, v in edges:
            graph[u].append(v)
            graph[v].append(u)

        visited = set()
        def dfs(node, parent):
            if node in visited:
                return False
            visited.add(node)
            for neighbor in graph[node]:
                if neighbor != parent and not dfs(neighbor, node):
                    return False
            return True

        return dfs(0, -1) and len(visited) == n
```
