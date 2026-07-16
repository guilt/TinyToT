# Class Generic

## python
```python
class Person:
    """A person with name, age, email."""

    def __init__(self, name: str, age: int, email: str | None = None) -> None:
        self.name = name
        self.age = age
        self.email = email

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Person({attrs})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Person):
            return NotImplemented
        return self.__dict__ == other.__dict__


# Example
obj = Person("Alice", 30, None)
print(obj)
```

### User variant

```python
class User:
    """A user with username, email, is_active."""

    def __init__(self, username: str, email: str, is_active: bool = True) -> None:
        self.username = username
        self.email = email
        self.is_active = is_active

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"User({attrs})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.__dict__ == other.__dict__
```

### Product variant

```python
class Product:
    """A product with name, price, quantity."""

    def __init__(self, name: str, price: float, quantity: int = 0) -> None:
        self.name = name
        self.price = price
        self.quantity = quantity

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Product({attrs})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return self.__dict__ == other.__dict__
```
