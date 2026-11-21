"""Tests for parametric-intent transform helpers."""

import math

import pytest

from pymodeler.core.parametric_transform import (
    apply_rotation_to_sketch_plane,
    apply_rotation_to_part_sketch_planes,
    apply_scale_to_sketch,
    apply_scale_to_part_sketches,
    apply_translation_to_sketch,
    apply_translation_to_part_sketches,
)
from pymodeler.core.sketch import create_rectangle_sketch, Sketch
from pymodeler.core.part import Part


def test_apply_translation_to_sketch_points_and_origin():
    sketch = create_rectangle_sketch(width=10.0, height=5.0)
    orig_origin = list(sketch.plane["origin"])
    pts_before = [(e["x"], e["y"]) for e in sketch.entities if e["type"] == "point"]

    apply_translation_to_sketch(sketch, dx=2.0, dy=-1.0, dz=0.5)

    assert sketch.plane["origin"] == pytest.approx([
        orig_origin[0] + 2.0,
        orig_origin[1] - 1.0,
        orig_origin[2] + 0.5,
    ])
    pts_after = [(e["x"], e["y"]) for e in sketch.entities if e["type"] == "point"]
    for (x0, y0), (x1, y1) in zip(pts_before, pts_after):
        assert x1 == pytest.approx(x0 + 2.0)
        assert y1 == pytest.approx(y0 - 1.0)
    sketch.validate()


def test_apply_translation_skips_fixed_points():
    sketch = Sketch()
    free = sketch.add_point(0.0, 0.0)
    fixed = sketch.add_point(5.0, 5.0, fixed=True)
    apply_translation_to_sketch(sketch, 1.0, 1.0)
    assert sketch.get_entity(free)["x"] == pytest.approx(1.0)
    assert sketch.get_entity(fixed)["x"] == pytest.approx(5.0)


def test_apply_translation_to_part_sketches():
    part = Part(name="Moved")
    sk = create_rectangle_sketch()
    part.add_sketch(sk)
    apply_translation_to_part_sketches(part, dx=3.0, dy=4.0)
    pts = [e for e in sk.entities if e["type"] == "point"]
    assert pts[0]["x"] == pytest.approx(3.0)  # rectangle starts at 0,0


def test_apply_scale_to_sketch_points_and_dimensions():
    sketch = create_rectangle_sketch(width=10.0, height=5.0)
    apply_scale_to_sketch(sketch, sx=2.0, sy=1.5)
    pts = [(e["x"], e["y"]) for e in sketch.entities if e["type"] == "point"]
    # original corners roughly (0,0), (10,0), (10,5), (0,5) -> scaled
    xs = sorted(p[0] for p in pts)
    ys = sorted(p[1] for p in pts)
    assert xs[-1] == pytest.approx(20.0)
    assert ys[-1] == pytest.approx(7.5)
    # length dims should have scaled by avg
    lengths = [d["value"] for d in sketch.dimensions if d["type"] == "length"]
    assert len(lengths) >= 2
    sketch.validate()


def test_apply_scale_skips_fixed_and_updates_radius():
    sketch = Sketch()
    free = sketch.add_point(2.0, 0.0)
    fixed = sketch.add_point(4.0, 0.0, fixed=True)
    cpt = sketch.add_point(0.0, 0.0)
    sketch.add_circle(cpt, 3.0)
    apply_scale_to_sketch(sketch, sx=2.0, sy=2.0)
    assert sketch.get_entity(free)["x"] == pytest.approx(4.0)
    assert sketch.get_entity(fixed)["x"] == pytest.approx(4.0)
    circ = [e for e in sketch.entities if e["type"] == "circle"][0]
    assert circ["radius"] == pytest.approx(6.0)


def test_apply_rotation_to_sketch_plane():
    sketch = Sketch()
    # identity plane
    assert sketch.plane["x_axis"] == pytest.approx([1.0, 0.0, 0.0])
    # 90 deg around Z
    apply_rotation_to_sketch_plane(sketch, 0.0, 0.0, math.pi / 2)
    # x_axis should become ~ [0, 1, 0]
    assert sketch.plane["x_axis"] == pytest.approx([0.0, 1.0, 0.0], abs=1e-6)
    assert sketch.plane["y_axis"] == pytest.approx([-1.0, 0.0, 0.0], abs=1e-6)
    sketch.validate()


def test_apply_scale_and_rotation_to_part():
    part = Part(name="Scaled")
    sk = create_rectangle_sketch(width=4.0, height=2.0)
    part.add_sketch(sk)
    apply_scale_to_part_sketches(part, sx=1.5, sy=1.5)
    apply_rotation_to_part_sketch_planes(part, 0.0, 0.0, 0.1)
    assert sk.plane["x_axis"] != pytest.approx([1.0, 0.0, 0.0])
    sk.validate()


def test_apply_translation_preserves_coincident_with_fixed():
    """A free point coincident with a fixed point must stay put (constraint-aware)."""
    sketch = Sketch()
    fixed = sketch.add_point(5.0, 5.0, fixed=True)
    free = sketch.add_point(5.0, 5.0)  # coincident position
    sketch.add_coincident(free, fixed)
    # also a truly free point
    loose = sketch.add_point(0.0, 0.0)

    apply_translation_to_sketch(sketch, dx=2.0, dy=3.0)

    assert sketch.get_entity(fixed)["x"] == pytest.approx(5.0)
    assert sketch.get_entity(free)["x"] == pytest.approx(5.0)  # locked by coincidence
    assert sketch.get_entity(loose)["x"] == pytest.approx(2.0)
    sketch.validate()


def test_apply_translation_respects_fixed_constraint():
    """A 'fixed' constraint on a point locks it even without the fixed flag."""
    sketch = Sketch()
    pt = sketch.add_point(1.0, 1.0)
    sketch.add_constraint("fixed", [pt])
    other = sketch.add_point(0.0, 0.0)

    apply_translation_to_sketch(sketch, 10.0, 10.0)

    assert sketch.get_entity(pt)["x"] == pytest.approx(1.0)
    assert sketch.get_entity(other)["x"] == pytest.approx(10.0)


def test_apply_scale_preserves_coincident_with_fixed():
    sketch = Sketch()
    fixed = sketch.add_point(2.0, 2.0, fixed=True)
    free = sketch.add_point(2.0, 2.0)
    sketch.add_coincident(free, fixed)
    loose = sketch.add_point(4.0, 0.0)

    apply_scale_to_sketch(sketch, sx=2.0, sy=2.0)

    assert sketch.get_entity(fixed)["x"] == pytest.approx(2.0)
    assert sketch.get_entity(free)["x"] == pytest.approx(2.0)
    assert sketch.get_entity(loose)["x"] == pytest.approx(8.0)
    sketch.validate()
