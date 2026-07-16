# Longest Common Prefix Trie

<\!-- Longest Common Prefix (Trie) Question Given a list of strings, find the longest common prefix using a Trie data structure. Example Input: ["flower", " -->

## python
```python
class TrieNode:

    def __init__(self):
        self.children = {}
        self.count = 0
        self.isEnd = False

    def insertWord(self, word: str) -> None:
        node = self
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.count += 1
        node.isEnd = True

    def findLongestCommonPrefix(self) -> str:
        node = self
        prefix = ""
        while node and len(node.children) == 1 and not node.isEnd:
            (char, nextNode), = node.children.items()
            if nextNode.count == len(words):
                prefix += char
                node = nextNode
            else:
                break
        return prefix


class Solution:

    def longestCommonPrefixTrie(self, words: list[str]) -> str:
        """
            Given a list of strings, find the longest common prefix using a Trie data structure.
        """
        root = TrieNode()
        root.insertWord([word for word in words])
        return root.findLongestCommonPrefix()
```
