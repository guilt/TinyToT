# Reg Ex Matcher

<\!-- RegEx Matcher Question Implement regular expression matching with support for ‘.’ and ‘*’. -->

## python
```python
from functools import cache

class Solution:
    @cache
    def isMatch(self, inputString: str, pattern: str) -> bool:
        """
            Implements regular expression matching with support for '.' and '*'.
        """
        if not pattern:
            return not inputString
        isFirstCharacterMatch = bool(inputString) and (pattern[0] == inputString[0] or pattern[0] == '.')
        if len(pattern) >= 2 and pattern[1] == '*':
            return (
                self.isMatch(inputString, pattern[2:]) or
                (isFirstCharacterMatch and self.isMatch(inputString[1:], pattern))
            )
        else:
            return isFirstCharacterMatch and self.isMatch(inputString[1:], pattern[1:])
```
