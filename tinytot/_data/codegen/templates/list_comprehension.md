# List Comprehension

## python
```python
# List comprehension general form:
# [expression for item in iterable if condition]

numbers = range(1, 11)

# All squares
squares = [n ** 2 for n in numbers]

# Even numbers only
evens = [n for n in numbers if n % 2 == 0]

# Even squares
even_squares = [n ** 2 for n in numbers if n % 2 == 0]

# Nested comprehension (flatten a 2D list)
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [x for row in matrix for x in row]
print(flat)  # [1, 2, 3, 4, 5, 6, 7, 8, 9]
```
