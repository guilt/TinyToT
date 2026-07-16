# Random1-5to1-7

<\!-- Random 1-5 to 1-7 Question Generate a random number between 1 and 7 using a random number generator that generates numbers between 1 and 5. -->

## python
```python
import random

class Solution:


    def rand5(self):
        """
        Returns a random number between 1 and 5.
        """
        return random.randint(1, 5)

    def rand7(self):
        """
        Returns a random number between 1 and 7 using rand5().
        """
        while True:
            num = (self.rand5() - 1) * 5 + self.rand5()
            if num <= 21:
                return num % 7 + 1

    def randM(self, m: int) -> int:
        """
        Returns a random number between 1 and m.
        """
        return random.randint(1, m)

    def randKGivenM(self, m: int, k: int) -> int:
        """
        Returns a random number between 1 and k using a random number
        generator that generates numbers between 1 and m.
        """
        while True:
            num = (self.randM(m) - 1) * m + self.randM(m)
            if num <= 1 + (m * (m - 1)):
                return num % k + 1
```
