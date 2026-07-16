# Letter Combinations Of Phone Number

<\!-- Letter Combinations of Phone Number Question Given a string containing digits from 2-9 inclusive, return all possible letter combinations that the num -->

## python
```python
from typing import List

class Solution:
    def generateLetterCombinations(self, inputDigits: str) -> List[str]:
        """
            Given a string containing digits from 2-9 inclusive, return all possible letter combinations that the number could represent.
        """
        if not inputDigits:
            return []

        digitToLetterMapping = {
            "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
            "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"
        }

        possibleCombinations = ['']

        for currentDigit in inputDigits:
            possibleCombinations = [
                currentCombination + letter
                for currentCombination in possibleCombinations
                for letter in digitToLetterMapping[currentDigit]
            ]

        return possibleCombinations
        return output
```
