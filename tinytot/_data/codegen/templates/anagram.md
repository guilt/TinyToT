# Anagram Check

## python
```python
def are_anagrams(s1: str, s2: str) -> bool:
    """Return True if s1 and s2 are anagrams of each other.

    Composition: sort both strings and compare (uses sort + compare).
    Or: count character frequencies and compare (uses Counter).
    """
    # Method 1: sort and compare  O(n log n)
    return sorted(s1.lower()) == sorted(s2.lower())


def are_anagrams_fast(s1: str, s2: str) -> bool:
    """Return True if anagrams. O(n) time using frequency count."""
    from collections import Counter
    return Counter(s1.lower()) == Counter(s2.lower())


# Examples
print(are_anagrams("listen", "silent"))   # True
print(are_anagrams("hello", "world"))     # False
print(are_anagrams("Astronomer", "Moon starer"))  # False (spaces differ)
```

## javascript
```javascript
function areAnagrams(s1, s2) {
    const normalize = s => s.toLowerCase().split('').sort().join('');
    return normalize(s1) === normalize(s2);
}

console.log(areAnagrams("listen", "silent")); // true
```

## go
```go
import "sort"

func areAnagrams(s1, s2 string) bool {
    r1 := []rune(strings.ToLower(s1))
    r2 := []rune(strings.ToLower(s2))
    sort.Slice(r1, func(i, j int) bool { return r1[i] < r1[j] })
    sort.Slice(r2, func(i, j int) bool { return r2[i] < r2[j] })
    return string(r1) == string(r2)
}
```
