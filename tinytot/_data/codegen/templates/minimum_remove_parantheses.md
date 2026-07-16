# Minimum Remove Parantheses

<\!-- Minimum Remove Parantheses Question Remove the minimum number of invalid parentheses in order to make the input string valid. -->

## python
```python
class Solution(object):
    def minRemoveToMakeValid(self, inputStr):
        """
        Returns a string with the minimum number of parentheses removed to make it valid.
        """
        def sortElements(elem):
            return elem[0]

        def cleanUpValid(s):
            idx = 0
            nestLevel = []
            while idx < len(s):
                charRead = s[idx]
                if charRead == '(':
                    nestLevel.append((idx, charRead))
                elif charRead == ')':
                    if nestLevel:
                        oldIndex, oldValue = nestLevel[-1]
                        del nestLevel[-1]
                        if oldValue == '(':
                            yield oldIndex, '('
                            yield idx, ')'
                else:
                    yield idx, charRead
                idx += 1

        sortedArray = sorted(cleanUpValid(inputStr), key=sortElements)
        sortedResults = ''.join([element[1] for element in sortedArray])
        return sortedResults
```
