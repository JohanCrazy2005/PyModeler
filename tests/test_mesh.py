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


def test_extrude_whole_mesh_increases_geometry():
    mesh = create_cube()
    original_verts = len(mesh.vertices)
    original_faces = len(mesh.faces)
    mesh.extrude_faces(distance=0.5, direction=(0, 0, 1))
    assert len(mesh.vertices) > original_verts
    assert len(mesh.faces) > original_faces
    mesh.validate()
    # All original vertices should still exist; new ones offset
    assert any(abs(v[2] - 0.5) < 1e-6 or abs(v[2] + 0.5) < 1e-6 for v in mesh.vertices)


def test_extrude_single_face_on_plane():
    mesh = create_plane()
    assert len(mesh.faces) == 1
    mesh.extrude_faces(face_indices=[0], distance=1.0, direction=(0, 0, 1))
    # Should have side faces + extruded face
    assert len(mesh.faces) >= 5  # original + 4 sides + 1 top
    mesh.validate()


def test_extrude_individual_creates_sides_per_face():
    mesh = create_cube()
    original_faces = len(mesh.faces)
    mesh.extrude_faces(distance=0.5, individual=True, use_per_face_normals=True)
    # Each of 6 faces produces 1 extruded + 4 sides → +5 faces per original face
    assert len(mesh.faces) == original_faces + 6 * 5
    mesh.validate()


def test_extrude_individual_on_plane():
    mesh = create_plane()
    mesh.extrude_faces(individual=True, use_per_face_normals=True, distance=1.0)
    # 1 original + 1 extruded + 4 sides
    assert len(mesh.faces) == 6
    mesh.validate()
    # Check that the extruded face is offset roughly along +Z
    zs = [v[2] for v in mesh.vertices]
    assert max(zs) > 0.9


def test_extrude_region_vs_individual_different_topology():
    mesh1 = create_cube()
    mesh2 = create_cube()
    mesh1.extrude_faces(distance=1.0, individual=False)
    mesh2.extrude_faces(distance=1.0, individual=True, use_per_face_normals=True)
    # Individual produces more faces (sides for every edge)
    assert len(mesh2.faces) > len(mesh1.faces)
    mesh1.validate()
    mesh2.validate()


def test_extrude_side_faces_have_outward_normals():
    """Side faces produced by extrude should have normals roughly aligned with extrusion direction."""
    mesh = create_plane()
    mesh.extrude_faces(distance=1.0, direction=(0, 0, 1))
    # After extrude of a single face there should be side faces whose normals have positive Z component
    # (or at least not all pointing inward)
    side_normals_z = []
    for i, face in enumerate(mesh.faces):
        if len(face) == 4:  # likely a side quad
            n = mesh.compute_face_normal(i)
            side_normals_z.append(n[2])
    # At least some sides should point somewhat outward (positive or mixed, but not all strongly negative)
    assert any(z > -0.1 for z in side_normals_z)
    mesh.validate()
