# Word Break2

<\!-- Word Break 2 Question Given a string s and a dictionary of words wordDict, add spaces in s to construct a sentence where each word is a valid dictiona -->

## python
```python
from typing import List
from functools import cache

class Solution:
    def wordBreak(self, inputString: str, wordDictionary: List[str]) -> List[str]:
        """
        Returns all possible sentences that can be constructed by adding spaces in the input string where each word is a valid dictionary word.
        """
        wordSet = set(wordDictionary)
        stringLength = len(inputString)

        @cache
        def buildSentences(startIndex: int) -> List[str]:
            if startIndex == stringLength:
                return [""]
            sentences = []
            for endIndex in range(startIndex + 1, stringLength + 1):
                word = inputString[startIndex:endIndex]
                if word in wordSet:
                    for subSentence in buildSentences(endIndex):
                        if subSentence:
                            sentences.append(f"{word} {subSentence}")
                        else:
                            sentences.append(word)
            return sentences

        return buildSentences(0)
```
