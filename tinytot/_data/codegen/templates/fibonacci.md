# Fibonacci

## python
```python
def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (iterative, O(n) time)."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


print(fibonacci(10))  # 55
print(fibonacci(20))  # 6765
```

## go
```go
func fibonacci(n int) int {
    if n <= 1 {
        return n
    }
    a, b := 0, 1
    for i := 2; i <= n; i++ {
        a, b = b, a+b
    }
    return b
}
```

## javascript
```javascript
function fibonacci(n) {
    if (n <= 1) return n;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) { [a, b] = [b, a + b]; }
    return b;
}
```

## typescript
```typescript
function fibonacci(n: number): number {
    if (n <= 1) return n;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) { [a, b] = [b, a + b]; }
    return b;
}
```

## rust
```rust
fn fibonacci(n: u64) -> u64 {
    if n <= 1 { return n; }
    let (mut a, mut b) = (0u64, 1u64);
    for _ in 2..=n {
        let c = a + b;
        a = b;
        b = c;
    }
    b
}
```

## cpp
```cpp
long long fibonacci(int n) {
    if (n <= 1) return n;
    long long a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        long long c = a + b;
        a = b; b = c;
    }
    return b;
}
```

## csharp
```csharp
static long Fibonacci(int n) {
    if (n <= 1) return n;
    long a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        long c = a + b; a = b; b = c;
    }
    return b;
}
```

## ruby
```ruby
def fibonacci(n)
  return n if n <= 1
  a, b = 0, 1
  (2..n).each { a, b = b, a + b }
  b
end

puts fibonacci(10)  # 55
```

## kotlin
```kotlin
fun fibonacci(n: Int): Long {
    if (n <= 1) return n.toLong()
    var a = 0L; var b = 1L
    (2..n).forEach { val c = a + b; a = b; b = c }
    return b
}
```

## swift
```swift
func fibonacci(_ n: Int) -> Int {
    if n <= 1 { return n }
    var (a, b) = (0, 1)
    for _ in 2...n { (a, b) = (b, a + b) }
    return b
}
```
