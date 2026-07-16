# Top K Frequent Elements

<\!-- Top K Frequent Elements Question Find the k most frequent elements in an array. -->

## python
```python
from collections import Counter
import heapq

class Solution:
    def topKFrequentElements(self, numberList, topKCount):
        """
        Returns the k most frequent elements in an array.
        """
        numberFrequencyMap = Counter(numberList)
        # Get the top K elements based on frequency
        return [element for element, _ in heapq.nlargest(topKCount, numberFrequencyMap.items(), key=lambda pair: pair[1])]
```
