# Replace Nth Consonant

<\!-- Replace Nth Consonant Question Given a string and an integer n , replace the n -th consonant in the string with the next consonant. Example Input: s = -->

## python
```python
class Solution:
    def replaceNthConsonant(self, s: str, n: int) -> str:
        """
        Replaces the n-th consonant in the string with the next consonant.
        """
        vowels = "aeiou"
        consonants = "bcdfghjklmnpqrstvwxyz"
        result = []
        count = 0
        for char in s:
            if char.lower() in consonants:
                if count == n:
                    result.append(consonants[(consonants.index(char.lower()) + 1) % len(consonants)])
                else:
                    result.append(char)
                count += 1
            else:
                result.append(char)
        return "".join(result)
```
