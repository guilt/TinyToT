# Generate N Paranthesis

<\!-- Generate N Paranthesis Question Generate all combinations of well-formed parentheses for N pairs. -->

## python
```python
from typing import List

class Solution:
    def generateParenthesis(self, numPairs: int) -> List[str]:
        """
            Generate all combinations of well-formed parentheses for N pairs.
        """
        resultList = []
        def backtrack(currentString = '', leftCount = 0, rightCount = 0):
            if len(currentString) == 2 * numPairs:
                resultList.append(currentString)
                return
            if leftCount < numPairs:
                backtrack(currentString + '(', leftCount + 1, rightCount)
            if rightCount < leftCount:
                backtrack(currentString + ')', leftCount, rightCount + 1)
        backtrack()
        return resultList
```
