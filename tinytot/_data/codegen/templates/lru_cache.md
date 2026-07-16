# L R U Cache

<\!-- LRU Cache Design and implement a data structure for Least Recently Used (LRU) cache with O(1) operations. Category: Hash Tables -->

## python
```python
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = Node(0, 0)  # Dummy head
        self.tail = Node(0, 0)  # Dummy tail
        self.head.next = self.tail
        self.tail.prev = self.head

    def addToEnd(self, node):
        prev = self.tail.prev
        prev.next = node
        node.prev = prev
        node.next = self.tail
        self.tail.prev = node

    def removeNode(self, node):
        prev = node.prev
        nxt = node.next
        prev.next = nxt
        nxt.prev = prev

    def moveToEnd(self, node):
        self.removeNode(node)
        self.addToEnd(node)

    def removeFirst(self):
        if self.head.next == self.tail:
            return None
        first = self.head.next
        self.removeNode(first)
        return first

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}  # key: Node
        self.dll = DoublyLinkedList()

    def get(self, key):
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self.dll.moveToEnd(node)
        return node.value

    def put(self, key, value):
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self.dll.moveToEnd(node)
        else:
            if len(self.cache) >= self.capacity:
                lru = self.dll.removeFirst()
                if lru:
                    del self.cache[lru.key]
            node = Node(key, value)
            self.cache[key] = node
            self.dll.addToEnd(node)
```
