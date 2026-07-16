# Dataclass

## python
```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Person:
    """A simple person dataclass with auto-generated __init__, __repr__, __eq__."""
    name: str
    age: int
    email: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def greet(self) -> str:
        return f"Hello, my name is {self.name} and I am {self.age} years old."


# Example
p = Person(name="Alice", age=30, email="alice@example.com")
print(p)                # Person(name='Alice', age=30, email='alice@example.com', tags=[])
print(p.greet())        # Hello, my name is Alice and I am 30 years old.
print(p == Person("Alice", 30))  # False (email differs)
```
