# Min Add To Make Valid Parens

<\!-- Paranthesis - Add to Make Valid Question Given a string S of ‘(‘ and ‘)’, add the minimum number of parentheses ( ‘(‘ or ‘)’, and in any positions ) s -->

## python
```python
class Solution:
    def minAddToMakeValid(self, parens: str) -> int:
        """
        Returns the minimum number of parentheses ( '(' or ')', and in any positions ) so that the resulting parentheses string is valid.
        """
        openNeeded = closeNeeded = 0
        for char in parens:
            if closeNeeded == 0 and char == ')':
                openNeeded += 1
            else:
                closeNeeded += 1 if char == '(' else -1
        return openNeeded + closeNeeded
```
