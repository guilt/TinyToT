# Custom Sort String

<\!-- Custom Sort String Question Given two strings S and T, sort T so that the order of characters matches S as much as possible. -->

## python
```python
import collections

class Solution:
    def customSortString(self, order: str, target: str) -> str:
        """
        Sorts string T so that the order of characters matches S as much as possible.
        Returns the sorted string.
        """
        targetCharCount = collections.Counter(target)
        result = []
        for char in order:
            if targetCharCount[char]:
                result.extend(char * targetCharCount[char])
                targetCharCount[char] = 0
        for char, count in targetCharCount.items():
            if count:
                result.extend(char * count)
        return ''.join(result)
```
