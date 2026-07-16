# Check If Number Is Palindrome

<\!-- Check if Number is Palindrome Question Determine whether an integer is a palindrome. -->

## python
```python
class Solution:
    def isPalindrome(self, originalNumber: int) -> bool:
        """
        Returns True if originalNumber is a palindrome, False otherwise.
        Negative numbers are not palindromes.
        """
        if originalNumber < 0:
            return False
        return str(originalNumber) == str(originalNumber)[::-1]
```
