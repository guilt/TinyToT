# Winning Lottery

<\!-- Winning Lottery Question Given a lottery problem with multiple possible solutions, use backtracking to find all valid combinations. Example Input: can -->

## python
```python
class Solution:
    def winningLottery(self, candidates: list[int], target: int) -> list[list[int]]:
        """
        Returns all combinations of candidates that sum to target (classic backtracking).
        """
        result = []
        def backtrack(remain, combo, start):
            if remain == 0:
                result.append(list(combo))
                return
            for i in range(start, len(candidates)):
                if candidates[i] > remain:
                    continue
                combo.append(candidates[i])
                backtrack(remain - candidates[i], combo, i)
                combo.pop()
        backtrack(target, [], 0)
        return result
```
