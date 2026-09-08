"""Finished animal contract (bananey).

coo + answers from files + says it cannot see.
This script is offline: it only checks the miss string and prints
how the sibling organs plug in. No server required.
"""
from tinytot.truth import MISS, decide

print(MISS)
assert decide(None, None) == MISS
assert decide(0.01, "noise") == MISS
print("tot miss: ok")
print("howl: tinyhowl coo /tmp/coo.wav")
print("ear:  tinyear ingest clip.wav --out memory/")
print("eye:  tinyeye examples/mug.jpg --out memory/ --no-latent")
print("pack: nanotot child --src tiny --out baby/")
print("watch: no camera. if no eye files, say the miss, not a caption.")
