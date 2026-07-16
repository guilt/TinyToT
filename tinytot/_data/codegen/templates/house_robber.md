# House Robber

<\!-- House Robber Problem Statement You are a professional robber planning to rob houses along a street. Each house has a certain amount of money stashed,  -->

## python
```python
from typing import List

class Solution:
    def rob(self, nums: List[int]) -> int:
        """
        Rob houses along a street.
        """
        prev1, prev2 = 0, 0

        for num in nums:
            temp = max(num + prev2, prev1)
            prev2 = prev1
            prev1 = temp

        return prev1
```
