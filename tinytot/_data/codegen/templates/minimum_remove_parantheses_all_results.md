# Minimum Remove Parantheses All Results

<\!-- Minimum Remove Parantheses All Results Question Remove the minimum number of invalid parentheses in order to make the input string valid. Return all p -->

## python
```python
class Solution:
    def removeInvalidParentheses(self, parenStr):
        """
        Returns all possible results after removing the minimum number of invalid parentheses in order to make the input string valid.
        """

        def dfs(currStr):
            minInvalid = countInvalid(currStr)
            if minInvalid == 0:
                results.append(currStr)
            for i in range(len(currStr)):
                if currStr[i] in ('(', ')'):
                    nextStr = currStr[:i] + currStr[i+1:]
                    if nextStr not in visited and countInvalid(nextStr) < minInvalid:
                        visited.add(nextStr)
                        dfs(nextStr)

        def countInvalid(parenStr):
            openCount = 0
            closeCount = 0
            for char in parenStr:
                openCount += {'(': 1, ')': -1}.get(char, 0)
                closeCount += openCount < 0
                openCount = max(openCount, 0)
            return openCount + closeCount

        visited = set([parenStr])
        results = []
        dfs(parenStr)

        return results
```
