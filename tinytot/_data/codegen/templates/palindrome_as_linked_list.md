# Palindrome As Linked List

<\!-- Palindrome as Linked List Question Check if a given linked list is a palindrome. Example Input: 1 - 2 - 3 - 2 - 1 Output: true -->

## python
```python
def isPalindrome(head: Optional[ListNode]) -> bool:
    if not head or not head.next:
        return True
    slow = head
    fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    prev = None
    while slow:
        next_node = slow.next
        slow.next = prev
        prev = slow
        slow = next_node
    while prev:
        if prev.val != head.val:
            return False
        prev = prev.next
        head = head.next
    return True
```
