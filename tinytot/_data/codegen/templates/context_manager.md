# Context Manager

## python
```python
from contextlib import contextmanager
import time


@contextmanager
def timer(label: str = ""):
    """Context manager that measures and prints elapsed time."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.4f}s" if label else f"Elapsed: {elapsed:.4f}s")


# Usage
with timer("data processing"):
    # your code here
    sum(range(1_000_000))


# Class-based alternative:
class ManagedResource:
    def __enter__(self):
        print("acquiring resource")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("releasing resource")
        return False  # do not suppress exceptions


with ManagedResource() as r:
    print("using resource")
```
