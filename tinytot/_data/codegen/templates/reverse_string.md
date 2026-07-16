# Reverse String

## python
```python
def reverse_string(s: str) -> str:
    """Return the reverse of string s."""
    return s[::-1]


# Example usage
print(reverse_string("hello"))  # "olleh"
```

## javascript
```javascript
function reverse_string(s) {
    return s.split('').reverse().join('');
}

// Example
console.log(reverse_string("hello")); // "olleh"
```

## java
```java
public static String reverse_string(String s) {
    return new StringBuilder(s).reverse().toString();
}
```

## go
```go
func reverseString(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}

// Example: fmt.Println(reverseString("hello")) // "olleh"
```

## rust
```rust
fn reverse_string(s: &str) -> String {
    s.chars().rev().collect()
}
```

## cpp
```cpp
#include <string>
#include <algorithm>

std::string reverseString(std::string s) {
    std::reverse(s.begin(), s.end());
    return s;
}

// Example: std::cout << reverseString("hello"); // "olleh"
```

## csharp
```csharp
public static string ReverseString(string s) {
    char[] chars = s.ToCharArray();
    System.Array.Reverse(chars);
    return new string(chars);
}

// Example: Console.WriteLine(ReverseString("hello")); // "olleh"
```

## ruby
```ruby
def reverse_string(s)
  s.reverse
end

puts reverse_string("hello")  # "olleh"
```

## kotlin
```kotlin
fun reverseString(s: String): String = s.reversed()

fun main() {
    println(reverseString("hello")) // "olleh"
}
```

## swift
```swift
func reverseString(_ s: String) -> String {
    return String(s.reversed())
}

print(reverseString("hello")) // "olleh"
```

## php
```php
<?php
function reverseString(string $s): string {
    return strrev($s);
}

echo reverseString("hello"); // "olleh"
```

## bash
```bash
#!/usr/bin/env bash
reverse_string() {
    echo "$1" | rev
}

reverse_string "hello"  # "olleh"
```
