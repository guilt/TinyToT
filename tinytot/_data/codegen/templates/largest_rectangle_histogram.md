# Largest Rectangle Histogram

<\!-- 82. Largest Rectangle in Histogram Question Given an array of integers representing the histogram’s bar width and height, return the area of the large -->

## python
```python
def largestRectangleArea(heights):
    stack = []
    maxArea = 0
    for i, h in enumerate(heights):
        while stack and h < heights[stack[-1]]:
            j = stack.pop()
            maxArea = max(maxArea, (i - stack[-1] - 1) * heights[j])
    return maxArea
```
