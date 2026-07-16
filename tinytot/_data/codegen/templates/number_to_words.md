# Number To Words

<\!-- Number to Words Question Convert a non-negative integer num to its English words representation. -->

## python
```python
def numberToWords(num):
    if num == 0:
        return "Zero"
    below20 = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "Ten", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    thousands = ["", "Thousand", "Million", "Billion"]

    def helper(n):
        if n == 0:
            return ""
        elif n < 20:
            return below20[n] + " "
        elif n < 100:
            return tens[n // 10] + " " + helper(n % 10)
        else:
            return below20[n // 100] + " Hundred " + helper(n % 100)

    result = ""
    for idx, unit in enumerate(thousands):
        if num % 1000 != 0:
            result = helper(num % 1000) + unit + " " + result
        num //= 1000
    return result.strip()
```
