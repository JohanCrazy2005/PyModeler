"""Tests for the parametric Sketch data model."""

import pytest

from pymodeler.core import (
    Sketch,
    create_rectangle_sketch,
    SketchValidationError,
    validate_sketch_data,
)


def test_empty_sketch_validates():
    sketch = Sketch(name="Empty")
    assert sketch.name == "Empty"
    assert len(sketch.entities) == 0
    sketch.validate()


def test_add_point_and_line():
    sketch = Sketch()
    p1 = sketch.add_point(0.0, 0.0)
    p2 = sketch.add_point(10.0, 0.0)
    line = sketch.add_line(p1, p2)
    assert sketch.get_entity(p1)["type"] == "point"
    assert sketch.get_entity(line)["type"] == "line"
    assert sketch.get_entity(line)["start_point"] == p1
    sketch.validate()


def test_add_circle_and_arc():
    sketch = Sketch()
    center = sketch.add_point(0.0, 0.0)
    circ = sketch.add_circle(center, 5.0)
    arc = sketch.add_arc(center, 3.0, 0.0, 1.57)
    assert sketch.get_entity(circ)["radius"] == 5.0
    assert sketch.get_entity(arc)["type"] == "arc"
    sketch.validate()


def test_constraints_and_dimensions():
    sketch = Sketch()
    p1 = sketch.add_point(0, 0)
    p2 = sketch.add_point(5, 0)
    line = sketch.add_line(p1, p2)
    sketch.add_horizontal(line)
    dim = sketch.add_length_dimension(line, 5.0)
    assert len(sketch.constraints) == 1
    assert len(sketch.dimensions) == 1
    assert sketch.dimensions[0]["value"] == 5.0
    sketch.validate()


def test_parameter_reference_in_dimension():
    sketch = Sketch()
    p1 = sketch.add_point(0, 0)
    p2 = sketch.add_point(10, 0)
    line = sketch.add_line(p1, p2)
    dim = sketch.add_length_dimension(line, "Width")
    assert sketch.dimensions[0]["value"] == "Width"
    sketch.validate()


def test_from_dict_roundtrip():
    original = create_rectangle_sketch(width=8.0, height=4.0, name="RectTest")
    data = original.to_dict()
    restored = Sketch.from_dict(data)
    assert restored.name == original.name
    assert len(restored.entities) == len(original.entities)
    assert len(restored.constraints) == len(original.constraints)
    assert len(restored.dimensions) == len(original.dimensions)
    # Check a dimension value survived
    lengths = [d["value"] for d in restored.dimensions if d["type"] == "length"]
    assert 8.0 in lengths
    assert 4.0 in lengths


def test_rectangle_factory_is_constrained():
    sketch = create_rectangle_sketch()
    assert len(sketch.entities) == 8  # 4 points + 4 lines
    assert len(sketch.constraints) >= 6  # horiz/vert + equals
    assert len(sketch.dimensions) == 2
    sketch.validate()
    data = sketch.to_dict()
    validate_sketch_data(data)


def test_invalid_sketch_raises():
    with pytest.raises(SketchValidationError):
        # Missing required fields
        Sketch.from_dict({"name": "bad"})


def test_get_entity_missing():
    sketch = Sketch()
    assert sketch.get_entity("nonexistent") is None
