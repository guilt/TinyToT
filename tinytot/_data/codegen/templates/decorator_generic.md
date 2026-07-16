# Decorator Generic

## python
```python
import functools


def my_decorator(func):
    """Generic decorator template."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Code before the function call
        result = func(*args, **kwargs)
        # Code after the function call
        return result
    return wrapper


@my_decorator
def example():
    return "hello"
```

### Memoize variant

```python
import functools


def memoize(func):
    """Simple memoization decorator using a dict cache."""
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    wrapper.cache = cache
    return wrapper


# Or use the standard library:
# from functools import lru_cache
# @lru_cache(maxsize=None)

@memoize
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

### Retry variant

```python
import functools
import time


def retry(max_attempts=3, delay=1.0):
    """Decorator that retries a function on exception."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


@retry(max_attempts=3, delay=0.5)
def unstable_operation():
    import random
    if random.random() < 0.7:
        raise ValueError("transient failure")
    return "success"
```

### Timeit variant

```python
import functools
import time


def timeit(func):
    """Decorator that prints the execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper


@timeit
def slow_function():
    time.sleep(0.1)
    return 42
```
