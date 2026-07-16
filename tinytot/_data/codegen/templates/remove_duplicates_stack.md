# Remove Duplicates Stack

<\!-- Remove Duplicates Using Stack Question Remove all adjacent duplicates in string s using a stack. -->

## python
```python
class Solution:
    def removeDuplicates(self, inputString: str) -> str:
        """
        Removes all adjacent duplicates in the input string using a stack.
        Returns the resulting string after all possible removals.
        """
        characterStack = []
        for character in inputString:
            if characterStack and characterStack[-1] == character:
                characterStack.pop()
            else:
                characterStack.append(character)
        return ''.join(characterStack)
```
