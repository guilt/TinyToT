# Group Encoded Strings

<\!-- Group Encoded Strings Question Group strings that are shifted versions of each other. -->

## python
```python
from typing import List

class Solution:
    def groupStrings(self, words: List[str]) -> List[List[str]]:
        """
        Groups strings that are shifted versions of each other.
        Returns a list of groups, each group is a list of strings.
        """
        groupMap = {}
        for word in words:
            shiftKey = ()
            for i in range(len(word) - 1):
                circularDiff = 26 + ord(word[i + 1]) - ord(word[i])
                shiftKey += (circularDiff % 26,)
            groupMap[shiftKey] = groupMap.get(shiftKey, []) + [word]
        return list(groupMap.values())
```
