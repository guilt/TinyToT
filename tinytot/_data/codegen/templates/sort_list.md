# Sort List

## python
```python
def sort_numbers(numbers: list[int]) -> list[int]:
    """Return a new sorted list (ascending). Does not modify the input."""
    return sorted(numbers)


# For in-place sort:
# numbers.sort()

# Example
print(sort_numbers([3, 1, 4, 1, 5, 9, 2, 6]))  # [1, 1, 2, 3, 4, 5, 6, 9]
```

## javascript
```javascript
function sort_numbers(numbers) {
    return [...numbers].sort((a, b) => a - b);
}

console.log(sort_numbers([3, 1, 4, 1, 5])); // [1, 1, 3, 4, 5]
```

## go
```go
func sortNumbers(numbers []int) []int {
    result := make([]int, len(numbers))
    copy(result, numbers)
    sort.Ints(result)
    return result
}
// import "sort" required
```

## rust
```rust
fn sort_numbers(mut numbers: Vec<i32>) -> Vec<i32> {
    numbers.sort();
    numbers
}

fn main() {
    let sorted = sort_numbers(vec![3, 1, 4, 1, 5, 9]);
    println!("{:?}", sorted); // [1, 1, 3, 4, 5, 9]
}
```

## cpp
```cpp
#include <vector>
#include <algorithm>

std::vector<int> sortNumbers(std::vector<int> numbers) {
    std::sort(numbers.begin(), numbers.end());
    return numbers;
}
```

## csharp
```csharp
using System;
using System.Linq;

int[] SortNumbers(int[] numbers) {
    var copy = (int[])numbers.Clone();
    Array.Sort(copy);
    return copy;
}
```

## ruby
```ruby
def sort_numbers(numbers)
  numbers.sort
end

p sort_numbers([3, 1, 4, 1, 5, 9])  # [1, 1, 3, 4, 5, 9]
```

## kotlin
```kotlin
fun sortNumbers(numbers: List<Int>): List<Int> = numbers.sorted()

fun main() {
    println(sortNumbers(listOf(3, 1, 4, 1, 5)))  // [1, 1, 3, 4, 5]
}
```

## swift
```swift
func sortNumbers(_ numbers: [Int]) -> [Int] {
    return numbers.sorted()
}

print(sortNumbers([3, 1, 4, 1, 5]))  // [1, 1, 3, 4, 5]
```
