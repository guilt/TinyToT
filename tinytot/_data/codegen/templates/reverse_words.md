# Reverse Words in a Sentence

## python
```python
def reverse_words(sentence: str) -> str:
    """Reverse the order of words in a sentence.

    Composition: split -> reverse -> join.
    """
    return ' '.join(sentence.split()[::-1])


def reverse_words_inplace(sentence: str) -> str:
    """Reverse words, preserving single spaces."""
    words = sentence.strip().split()
    return ' '.join(reversed(words))


# Examples
print(reverse_words("Hello World"))          # "World Hello"
print(reverse_words("  the sky  is blue "))  # "blue is sky the"
```

## javascript
```javascript
function reverseWords(sentence) {
    return sentence.trim().split(/\s+/).reverse().join(' ');
}

console.log(reverseWords("Hello World")); // "World Hello"
```

## go
```go
import "strings"

func reverseWords(s string) string {
    words := strings.Fields(s) // splits on any whitespace
    for i, j := 0, len(words)-1; i < j; i, j = i+1, j-1 {
        words[i], words[j] = words[j], words[i]
    }
    return strings.Join(words, " ")
}
```

## java
```java
public static String reverseWords(String s) {
    String[] words = s.trim().split("\\s+");
    StringBuilder sb = new StringBuilder();
    for (int i = words.length - 1; i >= 0; i--) {
        sb.append(words[i]);
        if (i > 0) sb.append(" ");
    }
    return sb.toString();
}
```
