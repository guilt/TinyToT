# Is Prime

## python
```python
def is_prime(n: int) -> bool:
    """Return True if n is a prime number.

    Uses trial division up to sqrt(n). O(sqrt(n)) time.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def sieve_of_eratosthenes(limit: int) -> list[int]:
    """Return all primes up to limit using the Sieve of Eratosthenes."""
    is_prime_arr = [True] * (limit + 1)
    is_prime_arr[0] = is_prime_arr[1] = False
    for i in range(2, int(limit ** 0.5) + 1):
        if is_prime_arr[i]:
            for j in range(i * i, limit + 1, i):
                is_prime_arr[j] = False
    return [i for i, p in enumerate(is_prime_arr) if p]


# Examples
print(is_prime(17))                    # True
print(is_prime(18))                    # False
print(sieve_of_eratosthenes(30))       # [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
```

## javascript
```javascript
function isPrime(n) {
    if (n < 2) return false;
    if (n === 2) return true;
    if (n % 2 === 0) return false;
    for (let i = 3; i * i <= n; i += 2) {
        if (n % i === 0) return false;
    }
    return true;
}
```

## go
```go
func isPrime(n int) bool {
    if n < 2 { return false }
    for i := 2; i*i <= n; i++ {
        if n%i == 0 { return false }
    }
    return true
}
```

## rust
```rust
fn is_prime(n: u64) -> bool {
    if n < 2 { return false; }
    if n == 2 { return true; }
    if n % 2 == 0 { return false; }
    let mut i = 3u64;
    while i * i <= n {
        if n % i == 0 { return false; }
        i += 2;
    }
    true
}
```
