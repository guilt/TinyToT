# Isomorphic Strings

<\!-- Isomorphic Strings Question Given two strings s and t, determine if they are isomorphic. Example Input: first = "egg", second = "add" Output: true -->

## python
```python
class Solution:
    def isIsomorphic(self, first: str, second: str) -> bool:
        """
        Determine if two strings are isomorphic.
        """
        if len(first) != len(second):
            return False

        charMap = {}
        for i in range(len(first)):
            if first[i] in charMap:
                if charMap[first[i]] != second[i]:
                    return False
            else:
                charMap[first[i]] = second[i]

        return True
```
