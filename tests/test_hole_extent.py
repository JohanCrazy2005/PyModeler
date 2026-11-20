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


def test_hole_direction_x_axis():
    """Direction [1,0,0] should orient the hole along X instead of Y."""
    feat = HoleFeature(diameter=4.0, depth=10.0, extent="blind", direction=[1.0, 0.0, 0.0], center=[0.0, 0.0, 0.0])
    mesh = feat.generate_mesh()
    xs = [v[0] for v in mesh.vertices]
    ys = [v[1] for v in mesh.vertices]
    zs = [v[2] for v in mesh.vertices]
    # Length should appear primarily along X
    x_span = max(xs) - min(xs)
    y_span = max(ys) - min(ys)
    z_span = max(zs) - min(zs)
    assert x_span == pytest.approx(10.0, abs=1e-4)
    # Diameter extents on the other axes should be ~4
    assert y_span == pytest.approx(4.0, abs=1e-3) or z_span == pytest.approx(4.0, abs=1e-3)
    feat.validate()
    restored = HoleFeature.from_dict(feat.to_dict())
    assert restored.direction == [1.0, 0.0, 0.0]
    restored.validate()


def test_hole_direction_negative_z():
    """Default-like direction [0,0,-1] should put length along Z."""
    feat = HoleFeature(diameter=2.0, depth=6.0, direction=[0.0, 0.0, -1.0])
    mesh = feat.generate_mesh()
    zs = [v[2] for v in mesh.vertices]
    z_span = max(zs) - min(zs)
    assert z_span == pytest.approx(6.0, abs=1e-4)
    feat.validate()
