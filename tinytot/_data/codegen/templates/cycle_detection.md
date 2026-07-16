# Floyd Cycle Detection (Linked List)

## python
```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def has_cycle(head: ListNode | None) -> bool:
    """Detect if a linked list has a cycle. O(n) time, O(1) space.

    Floyd's two-pointer algorithm: slow moves 1 step, fast moves 2 steps.
    If they meet, there is a cycle.
    """
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False


def find_cycle_start(head: ListNode | None) -> ListNode | None:
    """Return the node where the cycle begins, or None if no cycle."""
    slow = fast = head
    # Phase 1: detect cycle
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            break
    else:
        return None  # no cycle
    # Phase 2: find entry point
    slow = head
    while slow is not fast:
        slow = slow.next
        fast = fast.next
    return slow


# Build a cycle for testing:
# a -> b -> c -> d -> b (cycle at b)
a = ListNode(1); b = ListNode(2); c = ListNode(3); d = ListNode(4)
a.next = b; b.next = c; c.next = d; d.next = b
print(has_cycle(a))           # True
print(find_cycle_start(a).val) # 2
```

## javascript
```javascript
function hasCycle(head) {
    let slow = head, fast = head;
    while (fast && fast.next) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow === fast) return true;
    }
    return false;
}
```

## go
```go
func hasCycle(head *ListNode) bool {
    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
        if slow == fast { return true }
    }
    return false
}
```
