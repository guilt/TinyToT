# Original Alien Dictionary

<\!-- Original Alien Dictionary Question Given a list of words, find the order of characters in an alien language. -->

## python
```python
from collections import defaultdict, deque
from typing import List

def alienOrder(wordList: List[str]) -> str:
    """
    Determines the order of characters in an alien language given a sorted list of words.
    Returns a string representing the character order, or an empty string if invalid.
    """

    # Build the adjacency list and in-degree count for each character
    adjacencyMap = defaultdict(set)
    inDegreeMap = {character: 0 for word in wordList for character in word}

    for previousWord, nextWord in zip(wordList, wordList[1:]):
        for previousChar, nextChar in zip(previousWord, nextWord):
            if previousChar != nextChar:
                if nextChar not in adjacencyMap[previousChar]:
                    adjacencyMap[previousChar].add(nextChar)
                    inDegreeMap[nextChar] += 1
                break
        else:
            # If nextWord is a prefix of previousWord, the order is invalid
            if len(previousWord) > len(nextWord):
                return ""

    # Collect all characters with zero in-degree
    processingQueue = deque([character for character, degree in inDegreeMap.items() if degree == 0])
    characterOrder = []

    # Perform BFS/topological sort
    while processingQueue:
        currentChar = processingQueue.popleft()
        characterOrder.append(currentChar)
        for neighborChar in adjacencyMap[currentChar]:
            inDegreeMap[neighborChar] -= 1
            if inDegreeMap[neighborChar] == 0:
                processingQueue.append(neighborChar)

    # If all characters are included, return the order
    if len(characterOrder) == len(inDegreeMap):
        return "".join(characterOrder)
    else:
        return ""
```
