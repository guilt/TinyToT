# Reorganize String

<\!-- Reorganize String Question Rearrange the string so that no two adjacent characters are the same. -->

## python
```python
import collections

class Solution:
    def reorganizeString(self, inputString):
        if len(inputString) == 1:
            return inputString
        charFrequency = collections.Counter(inputString)
        mostFrequentChar = max(charFrequency.keys(), key=lambda x: charFrequency[x])
        resultList = [mostFrequentChar for _ in range(charFrequency[mostFrequentChar])]
        insertIndex = 0
        for char in charFrequency:
            if char != mostFrequentChar:
                for _ in range(charFrequency[char]):
                    resultList[insertIndex % len(resultList)] += char
                    insertIndex += 1
        resultString = ''.join(resultList)
        if insertIndex >= len(resultList) - 1:
            return resultString
        else:
            return ''
```
