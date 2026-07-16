# Generator

## python
```python
def infinite_counter(start: int = 0, step: int = 1):
    """Generator that yields an infinite sequence of numbers."""
    n = start
    while True:
        yield n
        n += step


def fibonacci_gen():
    """Generator that yields the Fibonacci sequence indefinitely."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def take(n: int, gen):
    """Take the first n values from a generator."""
    return [next(gen) for _ in range(n)]


# Examples
counter = infinite_counter(0, 2)
print(take(5, counter))       # [0, 2, 4, 6, 8]

fibs = fibonacci_gen()
print(take(10, fibs))         # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

# Generator expression (lazy evaluation)
squares = (n ** 2 for n in range(10))
print(list(squares))          # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```
