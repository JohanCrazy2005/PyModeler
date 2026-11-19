"""Tests for parametric-intent transform helpers."""

import pytest

from pymodeler.core.parametric_transform import (
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
