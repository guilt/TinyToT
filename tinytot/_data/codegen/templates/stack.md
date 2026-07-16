# Stack

## python
```python
class Stack:
    """LIFO stack backed by a Python list."""

    def __init__(self) -> None:
        self._items: list = []

    def push(self, item) -> None:
        """Push item onto the top of the stack."""
        self._items.append(item)

    def pop(self):
        """Remove and return the top item. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        """Return the top item without removing it."""
        if self.is_empty():
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"Stack({self._items})"


# Example
s = Stack()
s.push(1); s.push(2); s.push(3)
print(s.pop())   # 3
print(s.peek())  # 2
```

## javascript
```javascript
class Stack {
    constructor() {
        this._items = [];
    }
    push(item) { this._items.push(item); }
    pop() {
        if (this.isEmpty()) throw new Error("pop from empty stack");
        return this._items.pop();
    }
    peek() { return this._items[this._items.length - 1]; }
    isEmpty() { return this._items.length === 0; }
    get size() { return this._items.length; }
}
```
