# Two Sum

## python
```python
def two_sum(nums: list[int], target: int) -> list[int]:
    """Return indices of the two numbers that add up to target.

    Uses a hash map for O(n) time and O(n) space.
    Assumes exactly one solution exists.
    """
    seen: dict[int, int] = {}  # value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []


# Example
print(two_sum([2, 7, 11, 15], 9))   # [0, 1]
print(two_sum([3, 2, 4], 6))        # [1, 2]
```

## javascript
```javascript
function two_sum(nums, target) {
    const seen = new Map();
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (seen.has(complement)) return [seen.get(complement), i];
        seen.set(nums[i], i);
    }
    return [];
}
```

## go
```go
func twoSum(nums []int, target int) []int {
    seen := make(map[int]int)
    for i, num := range nums {
        if j, ok := seen[target-num]; ok {
            return []int{j, i}
        }
        seen[num] = i
    }
    return nil
}
```

## rust
```rust
use std::collections::HashMap;

fn two_sum(nums: Vec<i32>, target: i32) -> Vec<usize> {
    let mut seen: HashMap<i32, usize> = HashMap::new();
    for (i, &num) in nums.iter().enumerate() {
        if let Some(&j) = seen.get(&(target - num)) {
            return vec![j, i];
        }
        seen.insert(num, i);
    }
    vec![]
}
```

## cpp
```cpp
#include <unordered_map>
#include <vector>

std::vector<int> twoSum(std::vector<int>& nums, int target) {
    std::unordered_map<int,int> seen;
    for (int i = 0; i < (int)nums.size(); i++) {
        auto it = seen.find(target - nums[i]);
        if (it != seen.end()) return {it->second, i};
        seen[nums[i]] = i;
    }
    return {};
}
```

## csharp
```csharp
static int[] TwoSum(int[] nums, int target) {
    var seen = new Dictionary<int,int>();
    for (int i = 0; i < nums.Length; i++) {
        int complement = target - nums[i];
        if (seen.ContainsKey(complement)) return new[] {seen[complement], i};
        seen[nums[i]] = i;
    }
    return Array.Empty<int>();
}
```
