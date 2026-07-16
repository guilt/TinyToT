# Construct2 Buildings With Space

<\!-- Construct 2 Buildings with Space in Block of Size N Question Given an input number of sections N and each section has 2 plots on either sides of the r -->

## python
```python
from functools import lru_cache

@lru_cache(maxsize=None)
def Fib(n):
    if n <= 1:
        return n
    return Fib(n - 1) + Fib(n - 2)

def constructBuildingsWithSpace(n):
    return Fib(n + 2)**2
```
