# Meeting Rooms I I

<\!-- Meeting Rooms II Problem Statement Given an array of meeting time intervals where each interval is represented as a pair of integers [start, end], fin -->

## python
```python
import heapq
from typing import List

class Solution:
    def minMeetingRooms(self, intervals: List[List[int]]) -> int:
        if not intervals:
            return 0

        # Sort intervals by start time
        intervals.sort(key=lambda x: x[0])

        # Priority queue to store end times of meetings
        endTimes = []

        for interval in intervals:
            # If no rooms are available, use the room with the earliest end time
            if endTimes and endTimes[0] <= interval[0]:
                heapq.heappop(endTimes)

            # Add the current meeting's end time to the priority queue
            heapq.heappush(endTimes, interval[1])

        # The size of the priority queue is the minimum number of rooms needed
        return len(endTimes)
```
