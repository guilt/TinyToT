# GCD (Greatest Common Divisor)

## python
```python
def gcd(a: int, b: int) -> int:
    """Return the greatest common divisor of a and b (Euclidean algorithm)."""
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    """Return the least common multiple of a and b."""
    return a * b // gcd(a, b)


# Or use the standard library:
# from math import gcd, lcm

print(gcd(48, 18))   # 6
print(lcm(4, 6))     # 12
```

## javascript
```javascript
function gcd(a, b) {
    while (b) { [a, b] = [b, a % b]; }
    return a;
}

function lcm(a, b) { return (a * b) / gcd(a, b); }

console.log(gcd(48, 18)); // 6
```

## go
```go
func gcd(a, b int) int {
    for b != 0 {
        a, b = b, a%b
    }
    return a
}

func lcm(a, b int) int { return a / gcd(a, b) * b }
```

## rust
```rust
fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 { let t = b; b = a % b; a = t; }
    a
}
```

## c++
```cpp
int gcd(int a, int b) {
    while (b) { int t = b; b = a % b; a = t; }
    return a;
}
// Or: #include <numeric>  std::gcd(a, b)
```

## java
```java
public static int gcd(int a, int b) {
    while (b != 0) { int t = b; b = a % b; a = t; }
    return a;
}
```
