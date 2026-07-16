# Find Words That Can Be Formed By Characters

<\!-- Find Words That Can Be Formed by Characters Given an array of words and a string of characters, find all the words that can be formed using the charac -->

## python
```python
from collections import Counter
from itertools import permutations

class Solution:
    def findWordsByCount(self, wordList, charSet):
        """Iterate through wordList and check if each word can be formed from charSet using counts."""
        charsCount = Counter(charSet)
        result = []
        for word in wordList:
            wordCount = Counter(word)
            if all(wordCount[c] <= charsCount.get(c, 0) for c in wordCount):
                result.append(word)
        return result

    def findWords(self, wordList, charSet):
        """
        Returns a list of words that can be formed using the characters of the string using count-based checking only.
        Handles any Unicode characters efficiently.
        """
        return self.findWordsByCount(wordList, charSet)
```
