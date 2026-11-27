"""Tests for ShellFeature constant-thickness offset and Boolean path."""
import pytest

from pymodeler.core.features_more import ShellFeature, FeatureValidationError
from pymodeler.core.mesh import create_cube


def _mesh_volume(mesh):
    try:
        from pymodeler.core.boolean import _to_trimesh
        return float(abs(_to_trimesh(mesh).volume))
    except Exception:
        return None


def _has_boolean_engine():
    try:
        import trimesh, manifold3d  # noqa: F401
        return True
    except ImportError:
        return False


def test_shell_schema_validation():
    s = ShellFeature(thickness=2.0, name="TestShell")
    d = s.to_dict()
    assert d["type"] == "shell"
    ShellFeature.from_dict(d)


def test_shell_closed_inside_returns_mesh():
    cube = create_cube(size=10.0)
    result = ShellFeature(thickness=1.0, direction="inside", faces=[]).apply_to_mesh(cube)
    assert result is not None and len(result.faces) > 0


def test_shell_boolean_path_preferred_when_available():
    if not _has_boolean_engine():
        pytest.skip("manifold3d not available")
    cube = create_cube(size=10.0)
    result = ShellFeature(thickness=1.5, direction="inside", faces=[]).apply_to_mesh(cube)
    vol = _mesh_volume(result)
    assert vol is not None and 200 < vol < 1000


def test_shell_constant_thickness_volume_inside():
    if not _has_boolean_engine():
        pytest.skip("manifold3d not available")
    cube = create_cube(size=10.0)
    result = ShellFeature(thickness=1.0, direction="inside", faces=[]).apply_to_mesh(cube)
    vol = _mesh_volume(result)
    assert vol is not None and 300 < vol < 900


def test_shell_opening_produces_rim():
    cube = create_cube(size=10.0)
    result = ShellFeature(thickness=1.0, faces=["top"], direction="inside").apply_to_mesh(cube)
    assert result is not None and len(result.faces) >= len(cube.faces)


def test_shell_invalid_thickness_on_apply():
    with pytest.raises(FeatureValidationError):
        ShellFeature(thickness=-1.0).apply_to_mesh(create_cube(10.0))


def test_shell_offset_mesh_inward_helper():
    if not _has_boolean_engine():
        pytest.skip("manifold3d not available")
    inner = ShellFeature(thickness=1.0)._offset_mesh_inward(create_cube(10.0), 1.0)
    assert inner is not None
    vol = _mesh_volume(inner)
    assert vol is not None and 100 < vol < 1000


def test_shell_outside_returns_mesh():
    result = ShellFeature(thickness=1.0, direction="outside").apply_to_mesh(create_cube(10.0))
    assert result is not None and len(result.faces) > 0
