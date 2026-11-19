"""Tests for ExtrudeFeature, RevolveFeature, and FeatureHistory."""

import pytest

from pymodeler.core.features import (
    ExtrudeFeature,
    FeatureHistory,
    FeatureValidationError,
    HoleFeature,
    RevolveFeature,
    validate_extrude_data,
    validate_history_data,
    validate_hole_data,
    validate_revolve_data,
)
from pymodeler.core.parameters import ParameterStore
from pymodeler.core.sketch import create_rectangle_sketch


def test_extrude_numeric_distance():
    sketch = create_rectangle_sketch(width=10.0, height=5.0)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=3.0, name="Box")
    assert feat.type == "extrude"
    assert feat.resolved_distance() == 3.0
    mesh = feat.generate_mesh(sketch)
    assert len(mesh.vertices) == 8
    assert len(mesh.faces) == 6
    feat.validate()


def test_extrude_parameter_distance():
    sketch = create_rectangle_sketch(width=20.0, height=10.0)
    store = ParameterStore()
    store.add("Depth", value=8.0, unit="mm")
    store.add("DoubleDepth", expression="Depth * 2")
    feat = ExtrudeFeature(sketch_id=sketch.id, distance="DoubleDepth")
    assert feat.resolved_distance(store) == 16.0
    mesh = feat.generate_mesh(sketch, store)
    # Height of the box should be approximately the distance
    zs = [v[2] for v in mesh.vertices]
    assert max(zs) - min(zs) == pytest.approx(16.0)


def test_extrude_schema_roundtrip():
    feat = ExtrudeFeature(sketch_id="sketch_abc", distance="Height", symmetric=True)
    data = feat.to_dict()
    validate_extrude_data(data)
    restored = ExtrudeFeature.from_dict(data)
    assert restored.sketch_id == feat.sketch_id
    assert restored.distance == feat.distance
    assert restored.symmetric is True


def test_extrude_invalid_schema():
    with pytest.raises(FeatureValidationError):
        ExtrudeFeature.from_dict({"type": "extrude", "distance": 1.0})  # missing sketch_id


def test_feature_history_basic():
    sketch = create_rectangle_sketch()
    hist = FeatureHistory(name="Part1")
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=2.5)
    hist.add_extrude(feat)
    assert len(hist.features) == 1
    hist.validate()
    data = hist.to_dict()
    validate_history_data(data)
    restored = FeatureHistory.from_dict(data)
    assert len(restored.get_extrude_features()) == 1


def test_feature_history_recompute():
    sketch = create_rectangle_sketch(width=4.0, height=3.0)
    store = ParameterStore()
    store.add("H", value=6.0)
    hist = FeatureHistory()
    feat = ExtrudeFeature(sketch_id=sketch.id, distance="H")
    hist.add_extrude(feat)
    meshes = hist.recompute_meshes({sketch.id: sketch}, store)
    assert feat.id in meshes
    mesh = meshes[feat.id]
    assert len(mesh.vertices) == 8


def test_positive_distance_required():
    sketch = create_rectangle_sketch()
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=-1.0)
    with pytest.raises(FeatureValidationError):
        feat.generate_mesh(sketch)


def test_revolve_numeric_angle():
    sketch = create_rectangle_sketch(width=10.0, height=5.0)
    feat = RevolveFeature(sketch_id=sketch.id, angle=180.0, name="HalfTurn")
    assert feat.type == "revolve"
    assert feat.resolved_angle() == 180.0
    mesh = feat.generate_mesh(sketch)
    assert len(mesh.vertices) > 0
    assert len(mesh.faces) > 0
    feat.validate()


def test_revolve_parameter_angle():
    sketch = create_rectangle_sketch(width=8.0, height=4.0)
    store = ParameterStore()
    store.add("Angle", value=90.0, unit="deg")
    feat = RevolveFeature(sketch_id=sketch.id, angle="Angle")
    assert feat.resolved_angle(store) == 90.0
    mesh = feat.generate_mesh(sketch, store)
    assert len(mesh.vertices) > 8


def test_revolve_schema_roundtrip():
    feat = RevolveFeature(sketch_id="sketch_abc", angle="Turn", symmetric=True, segments=12)
    data = feat.to_dict()
    validate_revolve_data(data)
    restored = RevolveFeature.from_dict(data)
    assert restored.sketch_id == feat.sketch_id
    assert restored.angle == feat.angle
    assert restored.symmetric is True
    assert restored.segments == 12


def test_revolve_invalid_schema():
    with pytest.raises(FeatureValidationError):
        RevolveFeature.from_dict({"type": "revolve", "angle": 90.0})  # missing sketch_id


def test_revolve_in_history():
    sketch = create_rectangle_sketch()
    hist = FeatureHistory(name="PartWithRevolve")
    feat = RevolveFeature(sketch_id=sketch.id, angle=360.0)
    hist.add_revolve(feat)
    assert len(hist.features) == 1
    hist.validate()
    restored = FeatureHistory.from_dict(hist.to_dict())
    assert len(restored.get_revolve_features()) == 1
    meshes = hist.recompute_meshes({sketch.id: sketch})
    assert feat.id in meshes


def test_revolve_angle_bounds():
    sketch = create_rectangle_sketch()
    feat = RevolveFeature(sketch_id=sketch.id, angle=0.0)
    with pytest.raises(FeatureValidationError):
        feat.generate_mesh(sketch)
    feat2 = RevolveFeature(sketch_id=sketch.id, angle=400.0)
    with pytest.raises(FeatureValidationError):
        feat2.generate_mesh(sketch)


def test_extrude_start_offset():
    """Start offset shifts the extrusion along the direction."""
    sketch = create_rectangle_sketch(width=10.0, height=5.0)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=4.0, start_offset=2.0)
    mesh = feat.generate_mesh(sketch)
    zs = [v[2] for v in mesh.vertices]
    assert min(zs) == pytest.approx(2.0)
    assert max(zs) == pytest.approx(6.0)


def test_extrude_symmetric_with_offset():
    """Symmetric extrude centered on the offset position."""
    sketch = create_rectangle_sketch(width=10.0, height=5.0)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=6.0, symmetric=True, start_offset=1.0)
    mesh = feat.generate_mesh(sketch)
    zs = [v[2] for v in mesh.vertices]
    # half = 3, so from 1-3=-2 to 1+3=4
    assert min(zs) == pytest.approx(-2.0)
    assert max(zs) == pytest.approx(4.0)


def test_extrude_offset_parameter():
    sketch = create_rectangle_sketch()
    store = ParameterStore()
    store.add("Offset", value=1.5)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=3.0, start_offset="Offset")
    assert feat.resolved_start_offset(store) == 1.5
    mesh = feat.generate_mesh(sketch, store)
    zs = [v[2] for v in mesh.vertices]
    assert min(zs) == pytest.approx(1.5)
    assert max(zs) == pytest.approx(4.5)


def test_extrude_offset_schema_roundtrip():
    feat = ExtrudeFeature(sketch_id="s1", distance=5.0, start_offset="Off", symmetric=True)
    data = feat.to_dict()
    validate_extrude_data(data)
    restored = ExtrudeFeature.from_dict(data)
    assert restored.start_offset == "Off"
    assert restored.symmetric is True


def test_extrude_polygon_profile():
    """Extrude should use extracted polygon rather than just AABB when possible."""
    from pymodeler.core.sketch import Sketch
    sketch = Sketch(name="Triangle")
    # Simple triangle
    p1 = sketch.add_point(0, 0)
    p2 = sketch.add_point(4, 0)
    p3 = sketch.add_point(2, 3)
    sketch.add_line(p1, p2)
    sketch.add_line(p2, p3)
    sketch.add_line(p3, p1)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=2.0)
    mesh = feat.generate_mesh(sketch)
    assert len(mesh.vertices) == 6  # 3 bottom + 3 top
    assert len(mesh.faces) >= 5     # bottom, top, 3 sides


def test_extrude_circle_profile():
    """Circle entity should produce a faceted cylinder."""
    from pymodeler.core.sketch import Sketch
    sketch = Sketch(name="Circle")
    center = sketch.add_point(0, 0)
    sketch.add_circle(center, radius=5.0)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=3.0)
    mesh = feat.generate_mesh(sketch)
    # 24 segs * 2 rings + 2 centers
    assert len(mesh.vertices) > 40
    assert len(mesh.faces) > 20


def test_profile_extraction_arc_near_circle():
    from pymodeler.core.sketch import Sketch, extract_simple_profiles
    sketch = Sketch()
    c = sketch.add_point(0, 0)
    sketch.add_arc(c, radius=2.0, start_angle=0, end_angle=359)
    profs = extract_simple_profiles(sketch)
    assert any(p["type"] == "circle" for p in profs)


def test_hole_numeric():
    feat = HoleFeature(diameter=6.0, depth=10.0, name="M6Hole")
    assert feat.type == "hole"
    assert feat.resolved_diameter() == 6.0
    assert feat.resolved_depth() == 10.0
    mesh = feat.generate_mesh()
    assert len(mesh.vertices) > 20
    assert len(mesh.faces) > 10
    feat.validate()


def test_hole_parameter():
    store = ParameterStore()
    store.add("Dia", value=8.0)
    store.add("Dep", value=15.0)
    feat = HoleFeature(diameter="Dia", depth="Dep")
    assert feat.resolved_diameter(store) == 8.0
    assert feat.resolved_depth(store) == 15.0
    mesh = feat.generate_mesh(store)
    assert len(mesh.vertices) > 0


def test_hole_schema_roundtrip():
    feat = HoleFeature(diameter="D", depth=5.0, center=[1.0, 2.0], segments=16)
    data = feat.to_dict()
    validate_hole_data(data)
    restored = HoleFeature.from_dict(data)
    assert restored.diameter == "D"
    assert restored.depth == 5.0
    assert restored.center == [1.0, 2.0]
    assert restored.segments == 16


def test_hole_invalid_schema():
    with pytest.raises(FeatureValidationError):
        HoleFeature.from_dict({"type": "hole", "diameter": 1.0})  # missing depth


def test_hole_positive_required():
    feat = HoleFeature(diameter=0.0, depth=1.0)
    with pytest.raises(FeatureValidationError):
        feat.generate_mesh()
    feat2 = HoleFeature(diameter=1.0, depth=-1.0)
    with pytest.raises(FeatureValidationError):
        feat2.generate_mesh()


def test_hole_in_history():
    hist = FeatureHistory(name="WithHole")
    feat = HoleFeature(diameter=4.0, depth=8.0)
    hist.add_hole(feat)
    assert len(hist.features) == 1
    hist.validate()
    restored = FeatureHistory.from_dict(hist.to_dict())
    assert len(restored.get_hole_features()) == 1
    meshes = hist.recompute_meshes({})
    assert feat.id in meshes
    assert len(meshes[feat.id].vertices) > 0
