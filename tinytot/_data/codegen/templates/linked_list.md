# Linked List

## python
```python
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None


class LinkedList:
    """Singly linked list with append, prepend, delete, and search."""

    def __init__(self) -> None:
        self.head: Node | None = None

    def append(self, value) -> None:
        """Add value to the end of the list."""
        new_node = Node(value)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node

    def prepend(self, value) -> None:
        """Add value to the front of the list."""
        new_node = Node(value)
        new_node.next = self.head
        self.head = new_node

    def delete(self, value) -> bool:
        """Remove the first node with value. Returns True if found."""
        if not self.head:
            return False
        if self.head.value == value:
            self.head = self.head.next
            return True
        current = self.head
        while current.next:
            if current.next.value == value:
                current.next = current.next.next
                return True
            current = current.next
        return False

    def to_list(self) -> list:
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result

    def __repr__(self) -> str:
        return " -> ".join(str(v) for v in self.to_list())


# Example
ll = LinkedList()
ll.append(1); ll.append(2); ll.append(3)
ll.prepend(0)
print(ll)          # 0 -> 1 -> 2 -> 3
ll.delete(2)
print(ll)          # 0 -> 1 -> 3
```
