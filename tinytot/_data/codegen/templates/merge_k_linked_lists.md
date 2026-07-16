# Merge K Linked Lists

<\!-- Merge k Linked Lists Question Merge k sorted linked lists and return it as one sorted list. -->

## python
```python
import heapq
from typing import List, Optional

class ListNode:
    def __init__(self, val: int = 0, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next

class Solution:
    def mergeKLists(self, listOfLinkedLists: List[Optional[ListNode]]) -> Optional[ListNode]:
        """
        Merges k sorted linked lists and returns it as one sorted list.
        Uses a min-heap for efficient merging.
        """
        setattr(ListNode, "__lt__", lambda self, other: self.val <= other.val)
        minHeap = []
        for linkedListNode in listOfLinkedLists:
            if linkedListNode:
                heapq.heappush(minHeap, linkedListNode)
        dummyHeadNode = ListNode(None)
        currentMergedNode = dummyHeadNode
        while minHeap:
            smallestNode = heapq.heappop(minHeap)
            currentMergedNode.next = smallestNode
            currentMergedNode = currentMergedNode.next
            if smallestNode and smallestNode.next:
                heapq.heappush(minHeap, smallestNode.next)
        return dummyHeadNode.next
```
