# Longest Substring With K Distinct

<\!-- Longest Substring with Utmost K Distinct Characters Question Find the length of the longest substring that contains at most k distinct characters. -->

## python
```python
from typing import Dict

class Solution:
    def lengthOfLongestSubstringKDistinct(self, inputString: str, kDistinct: int) -> int:
        if kDistinct == 0 or not inputString:
            return 0

        leftPointer: int = 0
        maxLength: int = 0
        charFrequencyMap: Dict[str, int] = {}

        for rightPointer in range(len(inputString)):
            rightChar: str = inputString[rightPointer]
            charFrequencyMap[rightChar] = charFrequencyMap.get(rightChar, 0) + 1

            while len(charFrequencyMap) > kDistinct:
                leftChar: str = inputString[leftPointer]
                charFrequencyMap[leftChar] -= 1
                if charFrequencyMap[leftChar] == 0:
                    del charFrequencyMap[leftChar]
                leftPointer += 1

            maxLength = max(maxLength, rightPointer - leftPointer + 1)

        return maxLength
```
