"""Tests for ShellFeature stub."""

import pytest

from pymodeler.core.features import (
    ShellFeature,
    FeatureHistory,
    FeatureValidationError,
    validate_shell_data,
)
from pymodeler.core.parameters import ParameterStore
from pymodeler.core.mesh import create_cube


def test_shell_numeric_thickness():
    feat = ShellFeature(thickness=2.0, name="Walls")
    assert feat.type == "shell"
    assert feat.direction == "inside"
    assert feat.operation == "modify"
    assert feat.resolved_thickness() == 2.0
    mesh = feat.generate_mesh()
    assert len(mesh.vertices) > 0
    feat.validate()


def test_shell_parameter_thickness():
    store = ParameterStore()
    store.add("Wall", value=1.5)
    feat = ShellFeature(thickness="Wall")
    assert feat.resolved_thickness(store) == 1.5
    mesh = feat.generate_mesh(store)
    assert len(mesh.vertices) > 0


def test_shell_schema_roundtrip():
    feat = ShellFeature(thickness="Thick", faces=[0, 1], direction="outside", name="OpenShell")
    data = feat.to_dict()
    validate_shell_data(data)
    restored = ShellFeature.from_dict(data)
    assert restored.thickness == feat.thickness
    assert restored.faces == [0, 1]
    assert restored.direction == "outside"


def test_shell_invalid_schema():
    with pytest.raises(FeatureValidationError):
        ShellFeature.from_dict({"type": "shell"})  # missing thickness


def test_shell_apply_to_mesh_stub():
    base = create_cube(size=4.0)
    feat = ShellFeature(thickness=0.5)
    result = feat.apply_to_mesh(base)
    result.validate()
    # Stub currently returns a copy
    assert len(result.vertices) == len(base.vertices)
    assert len(result.faces) == len(base.faces)


def test_shell_history_integration():
    hist = FeatureHistory(name="Shelled")
    feat = ShellFeature(thickness=1.0)
    hist.add_shell(feat)
    assert len(hist.features) == 1
    hist.validate()
    meshes = hist.recompute_meshes({})
    assert feat.id in meshes
    assert len(meshes[feat.id].vertices) > 0


def test_shell_direction_and_faces():
    feat = ShellFeature(thickness=2.0, direction="both", faces=["top"])
    assert feat.direction == "both"
    assert feat.faces == ["top"]
    data = feat.to_dict()
    assert data["direction"] == "both"
    restored = ShellFeature.from_dict(data)
    assert restored.faces == ["top"]
