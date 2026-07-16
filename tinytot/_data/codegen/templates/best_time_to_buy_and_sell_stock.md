# Best Time To Buy And Sell Stock

<\!-- Best Time to Buy and Sell Stock Problem Statement You are given an array prices where prices[i] is the price of a given stock on the ith day. -->

## python
```python
from typing import List

class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        """
        Find the maximum profit that can be made by buying and selling a stock on different days.
        """
        maxProfit = 0
        minPrice = float('inf')

        for price in prices:
            if price < minPrice:
                minPrice = price
            elif price - minPrice > maxProfit:
                maxProfit = price - minPrice

        return maxProfit
```
