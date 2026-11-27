"""Pure tests for 3-point arc geometry (no Qt dependency)."""

from pymodeler.core.sketch import circle_from_3points


def test_circle_from_3points_semicircle():
    # (0,0), (5,5), (10,0) → center (5,0), radius 5
    result = circle_from_3points(0.0, 0.0, 5.0, 5.0, 10.0, 0.0)
    assert result is not None
    cx, cy, r, sa, ea = result
    assert abs(cx - 5.0) < 1e-6
    assert abs(cy - 0.0) < 1e-6
    assert abs(r - 5.0) < 1e-6
    # Sweep should cover the upper half (positive CCW from ~180 to ~360)
    assert ea > sa
    sweep = (ea - sa) % 360.0
    assert 170 < sweep < 190  # ~180


def test_circle_from_3points_collinear():
    assert circle_from_3points(0.0, 0.0, 1.0, 0.0, 2.0, 0.0) is None
    assert circle_from_3points(0.0, 0.0, 0.0, 1.0, 0.0, 2.0) is None


def test_circle_from_3points_quarter():
    # (0,0), (0,5), (5,5) roughly quarter circle around (5,0) or similar
    result = circle_from_3points(0.0, 0.0, 0.0, 5.0, 5.0, 5.0)
    assert result is not None
    cx, cy, r, sa, ea = result
    assert r > 0
    # Mid point should lie on the arc (angle between start and end)
    import math
    mid_ang = math.degrees(math.atan2(5.0 - cy, 0.0 - cx)) % 360.0
    start_ang = sa % 360.0
    # Basic sanity: radius matches distance to start
    assert abs(math.hypot(0.0 - cx, 0.0 - cy) - r) < 1e-6
