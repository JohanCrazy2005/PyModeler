"""Tests for ShellFeature."""

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


def test_shell_apply_to_mesh():
    base = create_cube(size=4.0)
    feat = ShellFeature(thickness=0.5)
    result = feat.apply_to_mesh(base)
    result.validate()
    # Basic shell should produce more geometry than the original solid
    assert len(result.vertices) > len(base.vertices)
    assert len(result.faces) > len(base.faces)
    # Thickness is reflected in the name
    assert "shell" in result.name


def test_shell_apply_with_opening():
    base = create_cube(size=4.0)
    # Open the top face (index 1 is the top face in create_cube)
    feat = ShellFeature(thickness=0.4, faces=[1])
    result = feat.apply_to_mesh(base)
    result.validate()
    assert len(result.vertices) > len(base.vertices)
    # Opening means fewer outer/inner faces than a fully closed shell
    closed = ShellFeature(thickness=0.4).apply_to_mesh(base)
    assert len(result.faces) < len(closed.faces)


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


def test_shell_mitered_corners():
    """Corner mitering should move vertices farther along the bisector than a pure normal offset."""
    base = create_cube(size=4.0)
    feat = ShellFeature(thickness=0.5, direction="inside")
    result = feat.apply_to_mesh(base)
    result.validate()
    # Original corner is at (2,2,2); after inside offset the corresponding inner vertex
    # should be closer to origin. With mitering the displacement is larger than pure normal.
    # Just ensure the shell is valid and has the expected extra geometry.
    assert len(result.vertices) == 2 * len(base.vertices)
    # Inner vertices exist and are not identical to outer
    n = len(base.vertices)
    outer = result.vertices[:n]
    inner = result.vertices[n:]
    assert outer[0] != inner[0]
    # A corner should have been offset by a non-trivial amount
    import numpy as np
    orig = np.asarray(base.vertices[6])  # a corner of the cube
    # Find the matching outer (should be same for inside)
    # For inside, outer_verts == base.vertices
    assert np.allclose(result.vertices[6], base.vertices[6])
    inner_corner = np.asarray(result.vertices[n + 6])
    displacement = np.linalg.norm(orig - inner_corner)
    # Pure normal offset would be ~0.5 / sqrt(3) ≈ 0.289; mitered is ~0.5
    assert displacement > 0.4


def test_shell_named_face_opening():
    """String face labels (top/bottom/...) resolve and produce an opening."""
    base = create_cube(size=4.0)
    feat = ShellFeature(thickness=0.3, faces=["top"])
    result = feat.apply_to_mesh(base)
    result.validate()
    closed = ShellFeature(thickness=0.3).apply_to_mesh(base)
    # Opening omits one outer + one inner face relative to closed shell
    assert len(result.faces) < len(closed.faces)
    # Named opening should match integer index of top face
    top_idx = None
    import numpy as np
    for i in range(len(base.faces)):
        n = np.asarray(base.compute_face_normal(i), dtype=float)
        if abs(n[2]) > 0.9 and n[2] > 0:
            top_idx = i
            break
    assert top_idx is not None
    feat_int = ShellFeature(thickness=0.3, faces=[top_idx])
    result_int = feat_int.apply_to_mesh(base)
    assert len(result.faces) == len(result_int.faces)


def test_shell_opening_has_rim_walls():
    """Openings must receive explicit rim walls (lip of thickness).

    Closed shell walls = all unique edges of the solid.
    With one open face, we still keep walls for the opening boundary (rim),
    so the face count is only reduced by the two omitted surfaces (outer+inner),
    not by the boundary walls.
    """
    base = create_cube(size=4.0)
    closed = ShellFeature(thickness=0.4).apply_to_mesh(base)
    open_shell = ShellFeature(thickness=0.4, faces=[1]).apply_to_mesh(base)
    closed.validate()
    open_shell.validate()
    # Closed: 6 outer + 6 inner + walls on 12 edges = 12 + 12 = 24 faces (quads)
    # Open one face: 5 outer + 5 inner + still walls on all 12 edges (rims included)
    # => 10 + 12 = 22 faces. Without rims it would be 10 + 8 = 18.
    assert len(closed.faces) == 24
    assert len(open_shell.faces) == 22
    # Rim presence: open shell has more faces than the no-rim estimate (18)
    assert len(open_shell.faces) > 18


def test_shell_string_index_face():
    """Face ids given as digit-strings are accepted."""
    base = create_cube(size=2.0)
    feat = ShellFeature(thickness=0.2, faces=["1"])
    result = feat.apply_to_mesh(base)
    result.validate()
    closed = ShellFeature(thickness=0.2).apply_to_mesh(base)
    assert len(result.faces) < len(closed.faces)
