# Distribute Money To Maximum Children

<\!-- Distribute Money to Maximum Children Problem Statement You are given an integer money denoting the amount of money (in dollars) that you have and anot -->

## python
```python
from typing import List

class Solution:
    def distributeMoney(self, money: int, children: List[int]) -> int:
        """
            Return the maximum number of children who may receive exactly 8 dollars if you distribute the money according to the aforementioned rules. If there is no way to distribute the money, return -1.
        """
        if money < children:
            return -1
        money -= children
        res = min(money // 7, children)
        money -= 7 * res
        remainingChildren = children - res
        if remainingChildren == 1 and money == 3:
            res -= 1
        elif remainingChildren == 0 and money > 0:
            res -= 1
        return res
```
