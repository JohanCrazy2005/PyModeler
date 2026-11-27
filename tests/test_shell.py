"""Tests for ShellFeature constant-thickness offset and Boolean path."""
import pytest

from pymodeler.core.features_more import ShellFeature, FeatureValidationError
from pymodeler.core.mesh import create_cube


def _mesh_volume(mesh):
    """Signed volume via trimesh; None if unavailable."""
    try:
        from pymodeler.core.boolean import _to_trimesh
        tm = _to_trimesh(mesh)
        return float(abs(tm.volume))
    except Exception:
        return None


def _has_boolean_engine():
    try:
        import trimesh  # noqa: F401
        import manifold3d  # noqa: F401
        return True
    except ImportError:
        return False


def test_shell_schema_validation():
    s = ShellFeature(thickness=2.0, name="TestShell")
    d = s.to_dict()
    assert d["type"] == "shell"
    assert d["thickness"] == 2.0
    ShellFeature.from_dict(d)


def test_shell_closed_inside_returns_mesh():
    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=1.0, direction="inside", faces=[])
    result = shell.apply_to_mesh(cube)
    assert result is not None
    assert len(result.faces) > 0
    assert len(result.vertices) >= len(cube.vertices)


def test_shell_boolean_path_preferred_when_available():
    """Closed inside shell should use Boolean cut when engine is present."""
    if not _has_boolean_engine():
        pytest.skip("manifold3d / Boolean engine not available")

    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=1.5, direction="inside", faces=[])
    result = shell.apply_to_mesh(cube)

    assert result is not None
    assert len(result.faces) > 0
    vol = _mesh_volume(result)
    # 10^3 - 7^3 = 1000 - 343 = 657
    assert vol is not None
    assert 600 < vol < 720


def test_shell_constant_thickness_volume_inside():
    """Inside shell of unit thickness on 10-cube should be ~488 (10^3 - 8^3)."""
    if not _has_boolean_engine():
        pytest.skip("manifold3d / Boolean engine not available")

    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=1.0, direction="inside", faces=[])
    result = shell.apply_to_mesh(cube)
    vol = _mesh_volume(result)
    assert vol is not None
    assert abs(vol - 488.0) < 5.0


def test_shell_constant_thickness_volume_outside():
    """Outside shell of unit thickness on 10-cube should be ~728 (12^3 - 10^3)."""
    if not _has_boolean_engine():
        pytest.skip("manifold3d / Boolean engine not available")

    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=1.0, direction="outside", faces=[])
    result = shell.apply_to_mesh(cube)
    vol = _mesh_volume(result)
    assert vol is not None
    assert abs(vol - 728.0) < 5.0


def test_shell_both_direction_volume():
    """Both direction with thickness 2 → half inside/out.

    half=1 → outer extents ~12, inner ~8 → 12^3-8^3=1728-512=1216.
    """
    if not _has_boolean_engine():
        pytest.skip("manifold3d / Boolean engine not available")

    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=2.0, direction="both", faces=[])
    result = shell.apply_to_mesh(cube)
    vol = _mesh_volume(result)
    assert vol is not None
    assert abs(vol - 1216.0) < 10.0


def test_shell_opening_produces_rim():
    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=1.0, faces=["top"], direction="inside")
    result = shell.apply_to_mesh(cube)
    assert result is not None
    # Openings remove outer faces (Boolean path) or add walls (wall-stitch)
    assert len(result.faces) >= len(cube.faces)


def test_shell_opening_removes_outer_faces_boolean():
    """With Boolean engine, opening should remove some outer faces vs closed shell."""
    if not _has_boolean_engine():
        pytest.skip("manifold3d / Boolean engine not available")

    cube = create_cube(size=10.0)
    closed = ShellFeature(thickness=1.0, direction="inside", faces=[])
    opened = ShellFeature(thickness=1.0, direction="inside", faces=["top"])
    r_closed = closed.apply_to_mesh(cube)
    r_opened = opened.apply_to_mesh(cube)
    assert len(r_opened.faces) < len(r_closed.faces)


def test_shell_invalid_thickness_on_apply():
    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=-1.0)
    with pytest.raises(FeatureValidationError):
        shell.apply_to_mesh(cube)


def test_shell_offset_mesh_helper():
    """_offset_mesh produces a smaller solid for inward offset."""
    if not _has_boolean_engine():
        pytest.skip("manifold3d / Boolean engine not available")

    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=1.0)
    inner = shell._offset_mesh(cube, 1.0, sign=-1.0)
    assert inner is not None
    vol_inner = _mesh_volume(inner)
    assert vol_inner is not None
    assert vol_inner < 1000.0  # original cube is 10^3
    assert abs(vol_inner - 512.0) < 5.0
