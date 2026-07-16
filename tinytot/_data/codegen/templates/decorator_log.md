# Decorator Log

## python
```python
import functools
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_calls(func):
    """Decorator that logs function name, arguments, and return value."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("Calling %s(args=%s, kwargs=%s)", func.__name__, args, kwargs)
        result = func(*args, **kwargs)
        logger.info("%s returned %s", func.__name__, result)
        return result
    return wrapper


@log_calls
def add(a, b):
    return a + b


# Example
add(3, 5)
# INFO: Calling add(args=(3, 5), kwargs={})
# INFO: add returned 8
```
