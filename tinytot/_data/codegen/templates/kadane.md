# Kadane Maximum Subarray

## python
```python
def max_subarray(nums: list[int]) -> int:
    """Return the maximum subarray sum (Kadane's algorithm). O(n) time.

    A subarray is a contiguous slice. Returns the sum, not the indices.
    To get the actual subarray, track start/end indices as shown below.
    """
    if not nums:
        return 0
    max_sum = current_sum = nums[0]
    for num in nums[1:]:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    return max_sum


def max_subarray_with_indices(nums: list[int]) -> tuple[int, int, int]:
    """Return (max_sum, start_idx, end_idx) of the maximum subarray."""
    max_sum = current_sum = nums[0]
    start = end = 0
    temp_start = 0
    for i in range(1, len(nums)):
        if nums[i] > current_sum + nums[i]:
            current_sum = nums[i]
            temp_start = i
        else:
            current_sum += nums[i]
        if current_sum > max_sum:
            max_sum = current_sum
            start = temp_start
            end = i
    return max_sum, start, end


# Examples
print(max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]))  # 6  (subarray [4,-1,2,1])
print(max_subarray([-1, -2, -3]))                       # -1 (all negative: pick max)
```

## javascript
```javascript
function maxSubarray(nums) {
    let maxSum = nums[0], currentSum = nums[0];
    for (let i = 1; i < nums.length; i++) {
        currentSum = Math.max(nums[i], currentSum + nums[i]);
        maxSum = Math.max(maxSum, currentSum);
    }
    return maxSum;
}

console.log(maxSubarray([-2, 1, -3, 4, -1, 2, 1, -5, 4])); // 6
```

## go
```go
func maxSubarray(nums []int) int {
    maxSum, cur := nums[0], nums[0]
    for _, n := range nums[1:] {
        if n > cur+n { cur = n } else { cur += n }
        if cur > maxSum { maxSum = cur }
    }
    return maxSum
}
```

## rust
```rust
fn max_subarray(nums: &[i32]) -> i32 {
    let (mut max_sum, mut cur) = (nums[0], nums[0]);
    for &n in &nums[1..] {
        cur = n.max(cur + n);
        max_sum = max_sum.max(cur);
    }
    max_sum
}
```

## java
```java
public static int maxSubarray(int[] nums) {
    int maxSum = nums[0], cur = nums[0];
    for (int i = 1; i < nums.length; i++) {
        cur = Math.max(nums[i], cur + nums[i]);
        maxSum = Math.max(maxSum, cur);
    }
    return maxSum;
}
```
