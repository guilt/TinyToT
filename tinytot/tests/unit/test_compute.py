"""Tests for tinytot.compute — relative-motion (precision-first) word problems.

These verify the structural-anchor contract: a solver must either produce a
correct answer from complete anchors (clock times + speeds + distance) or
refuse (return None) on prose it cannot fully determine.  Broad numeric prose
must NOT be attempted — the permissive solvers misfire on ~95% of real prose.
"""

from tinytot.compute import solveCompute, solvePreciseWordProblem

MEETING = (
    "A train leaves Station A at 2:00 PM traveling at 60 mph toward Station B, "
    "which is 150 miles away. Another train leaves Station B at 2:30 PM traveling "
    "at 50 mph toward Station A. At what clock time do the two trains meet?"
)
CATCHUP = (
    "Bus A leaves the depot at 9:00 AM going 40 mph. Bus B leaves the same depot "
    "at 9:30 AM going 70 mph. When does Bus B catch up with Bus A?"
)
LEG = "A cyclist travels at 15 mph for 4 hours. How far does she go?"
LEG_TIME = "How long does it take to drive 150 miles at 60 mph?"


class TestSolvePreciseWordProblem:
    def test_meeting_staggered_starts(self):
        out = solvePreciseWordProblem(MEETING)
        assert out is not None and "3:35 PM" in out
        assert "combined speed of 110" in out

    def test_meeting_simultaneous_starts(self):
        p = (
            "Two cars start at noon, 200 miles apart, driving toward each other "
            "at 40 mph and 60 mph. At what time do they meet?"
        )
        out = solvePreciseWordProblem(p)
        assert out is not None and "2:00 PM" in out

    def test_catch_up(self):
        out = solvePreciseWordProblem(CATCHUP)
        assert out is not None and "10:10 AM" in out

    def test_single_leg_distance(self):
        assert solvePreciseWordProblem(LEG) == "60 miles"

    def test_single_leg_time(self):
        assert solvePreciseWordProblem(LEG_TIME) == "2.50 hours"

    def test_refuses_round_trip_multileg(self):
        # Two rates + a return leg, no full meeting/catch-up anchors.
        p = (
            "Tom can travel at 10 miles per hour. He is sailing from 1 to 4 PM. "
            "He then travels back at a rate of 6 mph. How long does it take him to get back?"
        )
        assert solvePreciseWordProblem(p) is None

    def test_refuses_partial_price_prose(self):
        assert solvePreciseWordProblem("Buy 4 apples for $0.50 each. How much?") is None

    def test_refuses_catchup_when_later_slower(self):
        p = (
            "Bus A leaves at 9:00 AM going 60 mph. Bus B leaves at 9:30 AM going 40 mph. "
            "When does Bus B catch up with Bus A?"
        )
        assert solvePreciseWordProblem(p) is None

    def test_refuses_catchup_with_distance(self):
        p = (
            "Bus A leaves at 9:00 AM going 40 mph. Bus B leaves at 9:30 AM going 70 mph. "
            "They are 10 miles apart on the route. When does Bus B catch up?"
        )
        assert solvePreciseWordProblem(p) is None


class TestSolveComputeDispatch:
    def test_relative_motion_reachable_through_solve_compute(self):
        assert solveCompute(MEETING) is not None

    def test_solve_compute_still_handles_plain_arithmetic(self):
        assert solveCompute("what is 6 * 7") == "42"
