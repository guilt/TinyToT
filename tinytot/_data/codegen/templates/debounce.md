# Debounce

<\!-- Debounce Question Given a function fn and a time in milliseconds t, return a debounced version of that function. A debounced function is a function wh -->

## python
```python
import threading

class Solution:
    def debounce(self, func, delay):
        """
        Returns a debounced version of the given function.
        """
        timer = None
        def debounced(*args, **kwargs):
            nonlocal timer
            if timer:
                timer.cancel()
            timer = threading.Timer(delay / 1000, func, args=args, kwargs=kwargs)
            timer.start()
        return debounced
```
