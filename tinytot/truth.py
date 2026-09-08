"""tinytot.truth — one miss sentence. Absence is absence.

Self-benches measure consistency with the cache, not discovery of the world.
"""

from __future__ import annotations

MISS = "I don't know. That is not in my knowledge base."

# Same string everywhere so tests can grep it.
MISS_PREFIX = "I don't know."

DEFAULT_HIT_THRESHOLD = 0.12


def is_miss(text: str) -> bool:
    return (text or "").strip().startswith(MISS_PREFIX)


def miss() -> str:
    return MISS


def decide(score: float | None, passage: str | None, threshold: float = DEFAULT_HIT_THRESHOLD) -> str | None:
    """Return MISS when retrieval failed. Return None when the caller should answer from cache."""
    if not passage or not str(passage).strip():
        return MISS
    if score is None or score < threshold:
        return MISS
    return None
