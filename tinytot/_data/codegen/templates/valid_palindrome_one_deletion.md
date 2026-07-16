# Valid Palindrome One Deletion

<\!-- Valid Palindrome After One Deletion Question Given a string s, return true if the s can be palindrome after deleting at most one character from it. -->

## python
```python
class Solution:

    def _isPalindrome(self, inputString: str, leftIndex: int, rightIndex: int) -> tuple[int, int]:
        while leftIndex < rightIndex:
            if inputString[leftIndex] != inputString[rightIndex]:
                return leftIndex, rightIndex
            leftIndex += 1
            rightIndex -= 1
        return 0, 0

    def validPalindrome(self, inputString: str) -> bool:
        """
        Returns True if the given string can be a palindrome after deleting at most one character.
        """
        startIndex = 0
        endIndex = len(inputString) - 1
        startIndex, endIndex = self._isPalindrome(inputString, startIndex, endIndex)
        if (startIndex, endIndex) == (0, 0):
            return True
        return (
            self._isPalindrome(inputString, startIndex + 1, endIndex) == (0, 0)
            or self._isPalindrome(inputString, startIndex, endIndex - 1) == (0, 0)
        )
```
