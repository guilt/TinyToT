# FizzBuzz

## python
```python
def fizzbuzz(n: int) -> list[str]:
    """Return FizzBuzz sequence from 1 to n."""
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(i))
    return result


# One-liner version:
# ["FizzBuzz" if i%15==0 else "Fizz" if i%3==0 else "Buzz" if i%5==0 else str(i) for i in range(1,101)]

# Print FizzBuzz 1-100:
for line in fizzbuzz(100):
    print(line)
```

## javascript
```javascript
function fizzbuzz(n) {
    return Array.from({length: n}, (_, i) => {
        const k = i + 1;
        if (k % 15 === 0) return 'FizzBuzz';
        if (k % 3 === 0) return 'Fizz';
        if (k % 5 === 0) return 'Buzz';
        return String(k);
    });
}

fizzbuzz(100).forEach(x => console.log(x));
```

## go
```go
import "fmt"

func fizzbuzz(n int) {
    for i := 1; i <= n; i++ {
        switch {
        case i%15 == 0:
            fmt.Println("FizzBuzz")
        case i%3 == 0:
            fmt.Println("Fizz")
        case i%5 == 0:
            fmt.Println("Buzz")
        default:
            fmt.Println(i)
        }
    }
}
```

## java
```java
public static void fizzbuzz(int n) {
    for (int i = 1; i <= n; i++) {
        if (i % 15 == 0) System.out.println("FizzBuzz");
        else if (i % 3 == 0) System.out.println("Fizz");
        else if (i % 5 == 0) System.out.println("Buzz");
        else System.out.println(i);
    }
}
```

## rust
```rust
fn fizzbuzz(n: u32) {
    for i in 1..=n {
        match (i % 3, i % 5) {
            (0, 0) => println!("FizzBuzz"),
            (0, _) => println!("Fizz"),
            (_, 0) => println!("Buzz"),
            _      => println!("{}", i),
        }
    }
}
```
