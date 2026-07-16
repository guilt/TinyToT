# Palindrome

## python
```python
def is_palindrome(s: str) -> bool:
    """Return True if s reads the same forwards and backwards.

    Case-insensitive, ignores non-alphanumeric characters.
    """
    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]


# Examples
print(is_palindrome("racecar"))           # True
print(is_palindrome("A man a plan a canal Panama"))  # True
print(is_palindrome("hello"))             # False
```
