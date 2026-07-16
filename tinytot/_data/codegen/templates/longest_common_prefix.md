# Longest Common Prefix

<\!-- Longest Common Prefix Question Write a function to find the longest common prefix string amongst an array of strings. -->

## python
```python
class Solution:
    def longestCommonPrefix(self, stringList: List[str]) -> str:
        if not stringList:
            return ""
        shortestString = min(stringList, key=len)
        for charIndex, char in enumerate(shortestString):
            for otherString in stringList:
                if otherString[charIndex] != char:
                    return shortestString[:charIndex]
        return shortestString
```
