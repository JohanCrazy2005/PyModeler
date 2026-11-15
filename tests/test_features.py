"""Tests for ExtrudeFeature and FeatureHistory."""

import pytest

from pymodeler.core.features import (
    ExtrudeFeature,
    FeatureHistory,
    FeatureValidationError,
    validate_extrude_data,
    validate_history_data,
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
