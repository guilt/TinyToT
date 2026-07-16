# Reverse Words In String

<\!-- Reverse Words in a String Question Reverse the words in a given string. -->

## python
```python
class Solution:
    def reverseWords(self, inputString: str) -> str:
        """
        Reverses the order of words in the input string.
        Returns the string with word order reversed.
        """
        return ' '.join(inputString.split()[::-1])
```
