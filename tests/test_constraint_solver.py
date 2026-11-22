"""Tests for the lightweight constraint solver stub."""

import pytest

from pymodeler.core.constraint_solver import solve_sketch
from pymodeler.core.sketch import Sketch, create_rectangle_sketch


def test_horizontal_and_vertical_on_rectangle():
    sk = create_rectangle_sketch(width=10, height=5)
    # perturb free points a bit
    for ent in sk.entities:
        if ent["type"] == "point":
            ent["x"] += 0.3
            ent["y"] += 0.2
    res = solve_sketch(sk)
    assert res["success"]
    # After solve, opposite sides should be equal length and axes-aligned
    pts = {e["id"]: (e["x"], e["y"]) for e in sk.entities if e["type"] == "point"}
    lines = [e for e in sk.entities if e["type"] == "line"]
    # bottoms and tops should have nearly same y
    for ln in lines:
        a, b = pts[ln["start_point"]], pts[ln["end_point"]]
        # horizontal lines have same y, vertical same x (within tol)
        if abs(a[1] - b[1]) < 1e-4:
            assert abs(a[1] - b[1]) < 1e-5
        if abs(a[0] - b[0]) < 1e-4:
            assert abs(a[0] - b[0]) < 1e-5


def test_equal_length_and_coincident():
    sk = Sketch("eq")
    p1 = sk.add_point(0, 0, fixed=True)
    p2 = sk.add_point(3.2, 0.1)
    p3 = sk.add_point(6.1, 0.3)
    l1 = sk.add_line(p1, p2)
    l2 = sk.add_line(p2, p3)
    sk.add_equal(l1, l2)
    sk.add_horizontal(l1)
    sk.add_horizontal(l2)
    res = solve_sketch(sk)
    assert res["success"]
    # lengths should be nearly equal
    def length(line_id):
        ent = sk.get_entity(line_id)
        a = sk.get_entity(ent["start_point"])
        b = sk.get_entity(ent["end_point"])
        return ((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2) ** 0.5
    assert abs(length(l1) - length(l2)) < 1e-4


def test_parallel_perpendicular():
    sk = Sketch("par")
    p1 = sk.add_point(0, 0, fixed=True)
    p2 = sk.add_point(4, 0.2)
    p3 = sk.add_point(0.1, 3)
    p4 = sk.add_point(4.2, 3.1)
    l1 = sk.add_line(p1, p2)
    l2 = sk.add_line(p3, p4)
    sk.add_parallel(l1, l2)
    sk.add_horizontal(l1)
    res = solve_sketch(sk)
    assert res["success"]
    # both should be nearly horizontal
    for lid in (l1, l2):
        ent = sk.get_entity(lid)
        a = sk.get_entity(ent["start_point"])
        b = sk.get_entity(ent["end_point"])
        assert abs(b["y"] - a["y"]) < 1e-4


def test_fixed_points_untouched():
    sk = Sketch("fix")
    p1 = sk.add_point(1.0, 2.0, fixed=True)
    p2 = sk.add_point(5.0, 2.5)
    sk.add_line(p1, p2)
    sk.add_horizontal(sk.entities[-1]["id"])
    orig = (p1, sk.get_entity(p1)["x"], sk.get_entity(p1)["y"])
    solve_sketch(sk)
    ent = sk.get_entity(p1)
    assert abs(ent["x"] - orig[1]) < 1e-9
    assert abs(ent["y"] - orig[2]) < 1e-9


def test_already_satisfied():
    sk = create_rectangle_sketch()
    res = solve_sketch(sk)
    assert res["success"]
    assert res["cost"] < 1e-6


def test_length_dimension_drives_line():
    sk = Sketch("len")
    p1 = sk.add_point(0, 0, fixed=True)
    p2 = sk.add_point(3.0, 0.5)
    ln = sk.add_line(p1, p2)
    sk.add_horizontal(ln)
    sk.add_length_dimension(ln, 10.0)
    res = solve_sketch(sk)
    assert res["success"]
    ent = sk.get_entity(ln)
    a = sk.get_entity(ent["start_point"])
    b = sk.get_entity(ent["end_point"])
    length = ((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2) ** 0.5
    assert abs(length - 10.0) < 1e-4
    assert abs(b["y"] - a["y"]) < 1e-4


def test_distance_dimension():
    sk = Sketch("dist")
    p1 = sk.add_point(0, 0, fixed=True)
    p2 = sk.add_point(2.0, 1.0)
    sk.add_distance_dimension(p1, p2, 5.0)
    res = solve_sketch(sk)
    assert res["success"]
    a = sk.get_entity(p1)
    b = sk.get_entity(p2)
    dist = ((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2) ** 0.5
    assert abs(dist - 5.0) < 1e-4


def test_radius_dimension():
    sk = Sketch("rad")
    c = sk.add_point(0, 0, fixed=True)
    circ = sk.add_circle(c, 2.0)
    sk.add_radius_dimension(circ, 7.5)
    res = solve_sketch(sk)
    assert res["success"]
    assert abs(sk.get_entity(circ)["radius"] - 7.5) < 1e-4


def test_diameter_dimension():
    sk = Sketch("dia")
    c = sk.add_point(0, 0, fixed=True)
    circ = sk.add_circle(c, 3.0)
    sk.add_dimension("diameter", [circ], 12.0)
    res = solve_sketch(sk)
    assert res["success"]
    assert abs(sk.get_entity(circ)["radius"] - 6.0) < 1e-4


def test_driven_dimension_ignored():
    sk = Sketch("drv")
    p1 = sk.add_point(0, 0, fixed=True)
    p2 = sk.add_point(4.0, 0)
    ln = sk.add_line(p1, p2)
    sk.add_length_dimension(ln, 10.0)  # driving
    # add a driven one that shouldn't force anything extra
    sk.add_dimension("length", [ln], 99.0, driven=True)
    res = solve_sketch(sk)
    assert res["success"]
    ent = sk.get_entity(ln)
    a = sk.get_entity(ent["start_point"])
    b = sk.get_entity(ent["end_point"])
    length = ((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2) ** 0.5
    assert abs(length - 10.0) < 1e-3


def test_parameter_driven_length_dimension():
    from pymodeler.core.parameters import ParameterStore

    sk = Sketch("param_len")
    p1 = sk.add_point(0, 0, fixed=True)
    p2 = sk.add_point(3.0, 0.2)
    ln = sk.add_line(p1, p2)
    sk.add_horizontal(ln)
    sk.add_length_dimension(ln, "width")  # string parameter name

    params = ParameterStore()
    params.add("width", value=12.5)

    res = solve_sketch(sk, parameters=params)
    assert res["success"]
    ent = sk.get_entity(ln)
    a = sk.get_entity(ent["start_point"])
    b = sk.get_entity(ent["end_point"])
    length = ((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2) ** 0.5
    assert abs(length - 12.5) < 1e-4
    assert abs(b["y"] - a["y"]) < 1e-4


def test_parameter_driven_radius():
    from pymodeler.core.parameters import ParameterStore

    sk = Sketch("param_rad")
    c = sk.add_point(0, 0, fixed=True)
    circ = sk.add_circle(c, 1.0)
    sk.add_radius_dimension(circ, "rad")

    params = ParameterStore()
    params.add("rad", value=4.25)

    res = solve_sketch(sk, parameters=params)
    assert res["success"]
    assert abs(sk.get_entity(circ)["radius"] - 4.25) < 1e-4


def test_expression_driven_length_dimension():
    from pymodeler.core.parameters import ParameterStore

    sk = Sketch("expr_len")
    p1 = sk.add_point(0, 0, fixed=True)
    p2 = sk.add_point(3.0, 0.2)
    ln = sk.add_line(p1, p2)
    sk.add_horizontal(ln)
    sk.add_length_dimension(ln, "width * 2 + offset")  # expression

    params = ParameterStore()
    params.add("width", value=5.0)
    params.add("offset", value=2.5)

    res = solve_sketch(sk, parameters=params)
    assert res["success"]
    ent = sk.get_entity(ln)
    a = sk.get_entity(ent["start_point"])
    b = sk.get_entity(ent["end_point"])
    length = ((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2) ** 0.5
    assert abs(length - 12.5) < 1e-4
    assert abs(b["y"] - a["y"]) < 1e-4


def test_expression_driven_radius_with_parentheses():
    from pymodeler.core.parameters import ParameterStore

    sk = Sketch("expr_rad")
    c = sk.add_point(0, 0, fixed=True)
    circ = sk.add_circle(c, 1.0)
    sk.add_radius_dimension(circ, "(base + 1) * 2")

    params = ParameterStore()
    params.add("base", value=3.0)

    res = solve_sketch(sk, parameters=params)
    assert res["success"]
    assert abs(sk.get_entity(circ)["radius"] - 8.0) < 1e-4
