"""Tests for HoleFeature through_all extent."""
import pytest
from pymodeler.core.features import HoleFeature, validate_hole_data
from pymodeler.core.parameters import ParameterStore


def test_hole_through_all_default():
    feat = HoleFeature(diameter=5.0, depth=2.0, extent="through_all", name="ThroughHole")
    assert feat.extent == "through_all"
    assert feat.resolved_through_depth() == HoleFeature.DEFAULT_THROUGH_DEPTH
    mesh = feat.generate_mesh()
    ys = [v[1] for v in mesh.vertices]
    span = max(ys) - min(ys)
    assert span == pytest.approx(HoleFeature.DEFAULT_THROUGH_DEPTH, rel=1e-6)
    mid = (max(ys) + min(ys)) / 2.0
    assert mid == pytest.approx(0.0, abs=1e-6)
    feat.validate()
    data = feat.to_dict()
    assert data["extent"] == "through_all"
    assert "through_depth" not in data


def test_hole_through_all_explicit_depth():
    feat = HoleFeature(diameter=4.0, extent="through_all", through_depth=50.0)
    assert feat.resolved_through_depth() == 50.0
    mesh = feat.generate_mesh()
    ys = [v[1] for v in mesh.vertices]
    assert max(ys) - min(ys) == pytest.approx(50.0)
    restored = HoleFeature.from_dict(feat.to_dict())
    assert restored.extent == "through_all"
    assert restored.resolved_through_depth() == 50.0
    restored.validate()


def test_hole_through_all_parameter():
    store = ParameterStore()
    store.add("Thru", value=200.0)
    feat = HoleFeature(diameter=3.0, extent="through_all", through_depth="Thru")
    assert feat.resolved_through_depth(store) == 200.0
    mesh = feat.generate_mesh(store)
    ys = [v[1] for v in mesh.vertices]
    assert max(ys) - min(ys) == pytest.approx(200.0)


def test_hole_blind_still_starts_at_plane():
    feat = HoleFeature(diameter=6.0, depth=12.0, extent="blind", center=[1.0, 2.0, 3.0])
    mesh = feat.generate_mesh()
    ys = [v[1] for v in mesh.vertices]
    assert min(ys) == pytest.approx(3.0, abs=1e-6)
    assert max(ys) - min(ys) == pytest.approx(12.0)


def test_hole_schema_extent_roundtrip():
    data = {
        "id": "hole_test1",
        "type": "hole",
        "diameter": 5.0,
        "extent": "through_all",
        "through_depth": 80.0,
        "operation": "cut",
    }
    validate_hole_data(data)
    feat = HoleFeature.from_dict(data)
    assert feat.extent == "through_all"
    out = feat.to_dict()
    validate_hole_data(out)
