# Factorial

## python
```python
def factorial(n: int) -> int:
    """Return n! (n factorial). Raises ValueError for negative input."""
    if n < 0:
        raise ValueError("factorial is not defined for negative numbers")
    if n == 0:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


# Or use the standard library:
# from math import factorial

print(factorial(5))   # 120
print(factorial(10))  # 3628800
```
