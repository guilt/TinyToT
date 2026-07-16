# Shuffle Deck Of Cards

<\!-- Shuffle a Deck of Cards Question Shuffle a deck of cards using an algorithm with O(n) time complexity. This is also known as the Fisher-Yates shuffle  -->

## python
```python
import random
from typing import List

class Solution:
    def shuffleDeck(self, cardList: List[int]) -> None:
        """
        Shuffles the input list of cards in-place using the Fisher-Yates algorithm.
        """
        n = len(cardList)
        for i in range(n - 1, 0, -1):
            j = random.randint(0, i)
            cardList[i], cardList[j] = cardList[j], cardList[i]
```
