from tinytot.lru_bytes import ByteLRU

def test_evicts_oldest_when_over_budget():
    lru = ByteLRU[str, str](max_bytes=10)
    lru.put("a", "aa", 6)
    lru.put("b", "bb", 6)
    assert lru.get("a") is None
    assert lru.get("b") == "bb"
    assert lru.nbytes == 6

def test_touch_keeps_hot_key():
    lru = ByteLRU[str, str](max_bytes=10)
    lru.put("a", "aa", 6)
    assert lru.get("a") == "aa"
    lru.put("b", "bb", 6)
    assert lru.get("a") is None
