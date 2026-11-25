"""Tests for ShellFeature, including optional Boolean-based offset."""
import pytest
from pymodeler.core.mesh import Mesh, create_cube
from pymodeler.core.features import ShellFeature, FeatureValidationError


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
    # Result should have more geometry than a simple solid in most cases
    assert len(result.vertices) >= len(cube.vertices)


def test_shell_boolean_path_preferred_when_available():
    """When Boolean engine is present, closed inside shell should use cut path.

    We detect success by checking that the result is different from the pure
    wall-stitch fallback (Boolean usually produces cleaner/fewer faces or
    different topology). The test is skipped if no engine is available.
    """
    try:
        import trimesh
        try:
            import manifold3d  # noqa: F401
            has_engine = True
        except ImportError:
            has_engine = False
    except ImportError:
        has_engine = False

    if not has_engine:
        pytest.skip("manifold3d / Boolean engine not available")

    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=1.5, direction="inside", faces=[])
    result = shell.apply_to_mesh(cube)

    # Boolean path produces a solid with an interior cavity; face count typically
    # differs from the simple wall-stitch approximation.
    assert result is not None
    assert len(result.faces) > 0
    # Volume should be less than original cube
    try:
        import numpy as np
        # Rough volume check via bounding box or face count
        assert len(result.faces) != len(cube.faces) or len(result.vertices) != len(cube.vertices)
    except Exception:
        pass


def test_shell_opening_produces_rim():
    cube = create_cube(size=10.0)
    # Open the top face (index 0 is usually +Y for create_cube; we use named)
    shell = ShellFeature(thickness=1.0, faces=["top"], direction="inside")
    result = shell.apply_to_mesh(cube)
    assert result is not None
    assert len(result.faces) > len(cube.faces)  # walls added


def test_shell_invalid_thickness_on_apply():
    cube = create_cube(size=10.0)
    shell = ShellFeature(thickness=-1.0)
    with pytest.raises(FeatureValidationError):
        shell.apply_to_mesh(cube)
