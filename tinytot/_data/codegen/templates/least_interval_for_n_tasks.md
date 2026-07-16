# Least Interval For N Tasks

<\!-- Least Interval for N Tasks Question Find the least number of intervals the CPU will take to finish all the given tasks. -->

## python
```python
import collections
from typing import List

class Solution:
    def leastInterval(self, taskList: List[str], cooldown: int) -> int:
        taskFrequencies = collections.Counter(taskList)
        maxTaskFrequency = max(taskFrequencies.values())
        numMaxTasks = list(taskFrequencies.values()).count(maxTaskFrequency)
        return max(len(taskList), (maxTaskFrequency - 1) * (cooldown + 1) + numMaxTasks)
```
