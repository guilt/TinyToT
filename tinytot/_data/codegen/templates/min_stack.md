# Min Stack

<\!-- Min Stack Question Design a stack that supports push, pop, top, and retrieving the minimum element in constant time. -->

## python
```python
class MinStack:
    """
    Stack that supports push, pop, top, and retrieving the minimum element in constant time.
    """
    def __init__(self):
        self.stack = []
        self.minStack = []

    def push(self, val: int) -> None:
        """Pushes an element onto the stack."""
        self.stack.append(val)
        if not self.minStack or val <= self.minStack[-1]:
            self.minStack.append(val)

    def pop(self) -> None:
        """Removes the element on top of the stack."""
        if self.stack[-1] == self.minStack[-1]:
            self.minStack.pop()
        self.stack.pop()

    def top(self) -> int:
        """Gets the top element."""
        return self.stack[-1]

    def getMin(self) -> int:
        """Retrieves the minimum element in the stack."""
        return self.minStack[-1]
```
