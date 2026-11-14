"""Tests for Mesh data model and primitive generators."""

import pytest

from pymodeler.core import (
    Mesh,
    create_cube,
    create_plane,
    create_sphere,
    create_cylinder,
    create_cone,
    MeshValidationError,
    validate_mesh_data,
)


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


def test_create_plane_validates():
    mesh = create_plane()
    assert mesh.name == "Plane"
    assert len(mesh.vertices) == 4
    assert len(mesh.faces) == 1
    mesh.validate()


def test_plane_subdivisions():
    mesh = create_plane(subdivisions=2)
    assert len(mesh.vertices) == 9
    assert len(mesh.faces) == 4
    mesh.validate()


def test_create_sphere_validates():
    mesh = create_sphere(segments=8, rings=4)
    assert mesh.name == "Sphere"
    assert len(mesh.vertices) > 10
    assert len(mesh.faces) > 0
    mesh.validate()
    # Check approximate radius
    radii = [sum(v[i] ** 2 for i in range(3)) ** 0.5 for v in mesh.vertices]
    assert all(pytest.approx(1.0, abs=1e-6) == r for r in radii)


def test_create_cylinder_validates():
    mesh = create_cylinder(segments=8)
    assert mesh.name == "Cylinder"
    assert len(mesh.vertices) >= 16
    mesh.validate()


def test_create_cone_validates():
    mesh = create_cone(segments=8)
    assert mesh.name == "Cone"
    assert len(mesh.vertices) >= 9
    mesh.validate()


def test_primitives_are_schema_valid():
    for factory in (create_plane, create_sphere, create_cylinder, create_cone):
        mesh = factory()
        mesh.validate()
        data = mesh.to_dict()
        validate_mesh_data(data)
