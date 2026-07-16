# Minimum Cost For Tickets

<\!-- Minimum Cost For Tickets Question Find the minimum cost for tickets. Given a list of travel days and ticket costs, find the minimum cost needed to tra -->

## python
```python
from functools import lru_cache
from typing import List

class Solution:
    def minCostTickets(self, travelDays: List[int], ticketCosts: List[int]) -> int:
        numDays = len(travelDays)
        ticketDurations = [1, 7, 30]

        @lru_cache(None)
        def minCostFromDay(dayIndex):
            if dayIndex >= numDays:
                return 0
            minTotalCost = float('inf')
            nextDayIndex = dayIndex
            for ticketCost, ticketDuration in zip(ticketCosts, ticketDurations):
                while (
                    nextDayIndex < numDays
                    and travelDays[nextDayIndex] < travelDays[dayIndex] + ticketDuration
                ):
                    nextDayIndex += 1
                minTotalCost = min(
                    minTotalCost, minCostFromDay(nextDayIndex) + ticketCost
                )
            return minTotalCost

        return minCostFromDay(0)
```
