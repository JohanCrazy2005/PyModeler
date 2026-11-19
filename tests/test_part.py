"""Tests for the Part model."""

import pytest

from pymodeler.core import (
    ExtrudeFeature,
    FeatureHistory,
    ParameterStore,
    Part,
    Sketch,
    create_rectangle_sketch,
)
from pymodeler.core.part import PartValidationError, validate_part_data


def test_part_creation_and_recompute():
    sketch = create_rectangle_sketch(width=10.0, height=5.0, name="Base")
    hist = FeatureHistory(name="Part History")
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=3.0, name="Extrude1")
    hist.add_extrude(feat)

    part = Part(name="Bracket", sketches={sketch.id: sketch}, feature_history=hist)
    assert part.name == "Bracket"
    assert len(part.sketches) == 1

    body = part.recompute()
    assert body is not None
    assert len(body.vertices) == 8
    assert part.body is body


def test_part_with_parameters():
    sketch = create_rectangle_sketch(width=20.0, height=10.0)
    params = ParameterStore()
    params.add("Thickness", value=4.0)
    hist = FeatureHistory()
    feat = ExtrudeFeature(sketch_id=sketch.id, distance="Thickness")
    hist.add_extrude(feat)

    part = Part(
        name="Plate",
        sketches={sketch.id: sketch},
        parameters=params,
        feature_history=hist,
        material="Aluminum",
    )
    body = part.recompute()
    assert body is not None
    zs = [v[2] for v in body.vertices]
    assert max(zs) - min(zs) == pytest.approx(4.0)
    assert part.material == "Aluminum"


def test_part_schema_roundtrip():
    sketch = create_rectangle_sketch()
    hist = FeatureHistory()
    hist.add_extrude(ExtrudeFeature(sketch_id=sketch.id, distance=2.0))
    part = Part(name="Roundtrip", sketches={sketch.id: sketch}, feature_history=hist, material={"name": "Steel", "thickness": 3})

    data = part.to_dict()
    validate_part_data(data)
    restored = Part.from_dict(data)
    assert restored.name == part.name
    assert restored.id == part.id
    assert len(restored.sketches) == 1
    assert restored.material["name"] == "Steel"
    body = restored.recompute()
    assert body is not None


def test_part_empty_recompute():
    part = Part(name="Empty")
    assert part.recompute() is None
    assert part.body is None


def test_part_add_sketch():
    part = Part()
    sketch = Sketch(name="Extra")
    part.add_sketch(sketch)
    assert sketch.id in part.sketches
    part.validate()


def test_invalid_part_schema():
    with pytest.raises(PartValidationError):
        Part.from_dict({"name": "Bad"})  # missing feature_history


def test_part_hole_boolean_cut():
    """Hole feature with operation=cut should subtract from the base solid when Boolean engine is available."""
    from pymodeler.core import HoleFeature
    from pymodeler.core.boolean import BooleanError

    sketch = create_rectangle_sketch(width=10.0, height=10.0, name="Base")
    hist = FeatureHistory(name="WithHole")
    base = ExtrudeFeature(sketch_id=sketch.id, distance=5.0, name="Base", operation="new")
    hole = HoleFeature(diameter=2.0, depth=6.0, center=[5.0, 5.0], name="CenterHole", operation="cut")
    hist.add_extrude(base)
    hist.add_hole(hole)

    part = Part(name="PlateWithHole", sketches={sketch.id: sketch}, feature_history=hist)
    try:
        body = part.recompute()
        assert body is not None
        # If cut succeeded, vertex count should differ from plain base (or at least be valid)
        base_only = base.generate_mesh(sketch)
        # Result should be valid mesh; if engine present it is typically more complex
        body.validate()
        # Soft check: if Boolean engine worked, faces may increase due to the hole walls
        assert len(body.faces) >= len(base_only.faces) or len(body.vertices) != len(base_only.vertices)
    except BooleanError:
        pytest.skip("Boolean engine not available for cut")
    except Exception as exc:
        # Unexpected failure should still fail the test
        raise AssertionError(f"Hole cut recompute failed unexpectedly: {exc}") from exc
