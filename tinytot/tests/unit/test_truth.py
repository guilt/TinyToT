from tinytot.truth import MISS, decide, is_miss, miss


def test_miss_is_stable():
    assert miss() == MISS
    assert is_miss(MISS)
    assert not is_miss("Paris is the capital of France.")


def test_decide_no_passage():
    assert decide(0.9, None) == MISS
    assert decide(0.9, "") == MISS


def test_decide_low_score():
    assert decide(0.01, "something") == MISS


def test_decide_hit():
    assert decide(0.5, "A mug on a desk.") is None
