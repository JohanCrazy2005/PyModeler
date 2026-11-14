"""Tests for Mesh data model and cube primitive."""

import pytest

from pymodeler.core import Mesh, create_cube, MeshValidationError, validate_mesh_data


def test_create_cube_validates():
    mesh = create_cube()
    assert mesh.name == "Cube"
    assert len(mesh.vertices) == 8
    assert len(mesh.faces) == 6
    mesh.validate()  # should not raise


def test_cube_size():
    mesh = create_cube(size=4.0)
    # vertices should span from -2 to +2
    xs = [v[0] for v in mesh.vertices]
    assert min(xs) == pytest.approx(-2.0)
    assert max(xs) == pytest.approx(2.0)


def test_invalid_mesh_raises():
    with pytest.raises(MeshValidationError):
        Mesh(vertices=[[0, 0, 0]], faces=[[0, 1, 2]])  # too few vertices


def test_from_dict_roundtrip():
    original = create_cube(name="TestCube")
    data = original.to_dict()
    restored = Mesh.from_dict(data)
    assert restored.name == original.name
    assert restored.vertices == original.vertices
    assert restored.faces == original.faces
