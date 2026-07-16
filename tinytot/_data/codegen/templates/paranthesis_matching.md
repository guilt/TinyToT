# Paranthesis Matching

<\!-- Paranthesis Matching Question Check if a string containing ‘(‘, ‘)’, ‘{‘, ‘}’, ‘[’ and ‘]’ is valid. -->

## python
```python
class Solution:
    def isValid(self, parenString: str) -> bool:
        """
            Check if a string containing '(', ')', '{', '}', '[' and ']' is valid.
        """
        stack = []
        closingToOpening = {')': '(', '}': '{', ']': '['}
        for char in parenString:
            if char in closingToOpening.values():
                stack.append(char)
            elif char in closingToOpening:
                topElement = stack.pop() if stack else '#'
                if closingToOpening[char] != topElement:
                    return False
        return not stack
```
