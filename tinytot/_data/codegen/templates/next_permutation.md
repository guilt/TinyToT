# Next Permutation

<\!-- Next Permutation (C++ std::next_permutation Implementation) Question Given a sequence of numbers, rearrange them into the lexicographically next great -->

## python
```python
from typing import List

class Solution:
    def nextPermutation(self, numberList: List[int]) -> None:
        """
        Modifies numberList in-place to its next lexicographical permutation.
        """
        i = len(numberList) - 2
        while i >= 0 and numberList[i] >= numberList[i + 1]:
            i -= 1
        if i >= 0:
            j = len(numberList) - 1
            while numberList[j] <= numberList[i]:
                j -= 1
            numberList[i], numberList[j] = numberList[j], numberList[i]
        numberList[i + 1:] = reversed(numberList[i + 1:])
```
