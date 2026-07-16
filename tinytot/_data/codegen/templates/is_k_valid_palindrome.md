# Is K Valid Palindrome

<\!-- Is K Valid Palindrome Question Check if a string can be transformed into a palindrome by removing at most k characters. -->

## python
```python
class Solution:
    def isValidPalindrome(self, inputString: str, maxRemovals: int) -> bool:
        stringLength = len(inputString)
        minimumRemovals = [[0] * (stringLength + 1) for _ in range(stringLength + 1)]
        for substringLength in range(stringLength + 1):
            for leftIndex in range(stringLength + 1):
                rightIndex = stringLength - leftIndex
                if leftIndex == 0 or rightIndex == 0:
                    minimumRemovals[leftIndex][rightIndex] = leftIndex or rightIndex
                elif inputString[leftIndex - 1] == inputString[rightIndex - 1]:
                    minimumRemovals[leftIndex][rightIndex] = minimumRemovals[leftIndex - 1][rightIndex - 1]
                else:
                    minimumRemovals[leftIndex][rightIndex] = 1 + min(minimumRemovals[leftIndex - 1][rightIndex], minimumRemovals[leftIndex][rightIndex - 1])
        return minimumRemovals[stringLength][stringLength] <= maxRemovals * 2
```
