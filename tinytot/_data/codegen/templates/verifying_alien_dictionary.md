# Verifying Alien Dictionary

<\!-- Verifying an Alien Dictionary Question LeetCode Here -->

## python
```python
from typing import List

class Solution:
    def isAlienSorted(self, wordList: List[str], orderString: str) -> bool:
        """
        Returns True if the given list of words is sorted according to the rules of an alien language.
        """
        charOrderMap = {char: idx for idx, char in enumerate(orderString)}
        for wordIndex in range(len(wordList) - 1):
            for charIndex in range(len(wordList[wordIndex])):
                # If no mismatch is found, check for prefix case (e.g., "apple", "app")
                if charIndex >= len(wordList[wordIndex + 1]):
                    return False
                if wordList[wordIndex][charIndex] != wordList[wordIndex + 1][charIndex]:
                    if charOrderMap[wordList[wordIndex][charIndex]] > charOrderMap[wordList[wordIndex + 1][charIndex]]:
                        return False
                    break
        return True
```
