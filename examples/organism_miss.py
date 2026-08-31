from tinytot.truth import MISS, decide
print(MISS)
assert decide(None, None) == MISS
assert decide(0.01, "noise") == MISS
print("ok")
