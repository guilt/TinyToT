# Singleton

## python
```python
class Singleton:
    """Thread-safe singleton using __new__."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value=None):
        # __init__ is called every time, but __new__ returns the same instance
        if not hasattr(self, "_initialized"):
            self.value = value
            self._initialized = True


# Example
a = Singleton("first")
b = Singleton("second")
print(a is b)        # True — same instance
print(a.value)       # "first" — value set only once
```
