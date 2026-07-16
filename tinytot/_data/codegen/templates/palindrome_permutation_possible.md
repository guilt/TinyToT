# Palindrome Permutation Possible

<\!-- Palindrome Permutation Possible Question Given a string, check if it can be rearranged to form a palindrome. Example Input: “aabbcc” Output: True -->

## python
```python
from collections import Counter

class Solution:
    def canPermutePalindrome(self, inputString: str) -> bool:
        """
        Returns True if the input string can be permuted to form a palindrome.
        """
        charCount = Counter(inputString)
        oddCount = sum(1 for count in charCount.values() if count % 2 == 1)
        return oddCount <= 1
```
