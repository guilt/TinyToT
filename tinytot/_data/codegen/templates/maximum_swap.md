# Maximum Swap

<\!-- Maximum Swap Question Given a non-negative integer, you can swap two digits at most once to get the maximum valued number. -->

## python
```python
class Solution:
    def maximumSwap(self, inputNumber: int) -> int:
        """
        Swaps two digits at most once to get the maximum valued number.
        Returns the maximum valued number.
        """
        numberCharList = list(str(inputNumber))
        lastDigitIndexMap = {int(digit): index for index, digit in enumerate(numberCharList)}
        for currentIndex, currentDigitChar in enumerate(numberCharList):
            currentDigit = int(currentDigitChar)
            for candidateDigit in range(9, currentDigit, -1):
                if lastDigitIndexMap.get(candidateDigit, -1) > currentIndex:
                    swapIndex = lastDigitIndexMap[candidateDigit]
                    numberCharList[currentIndex], numberCharList[swapIndex] = numberCharList[swapIndex], numberCharList[currentIndex]
                    return int(''.join(numberCharList))
        return inputNumber
```
