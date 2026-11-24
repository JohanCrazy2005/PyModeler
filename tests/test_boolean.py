"""Tests for mesh Boolean helpers and FeatureHistory integration."""

import pytest

from pymodeler.core.mesh import Mesh, create_cube, create_cylinder
from pymodeler.core.boolean import mesh_boolean, BooleanError
from pymodeler.core.features import ExtrudeFeature, FeatureHistory
from pymodeler.core.sketch import Sketch, create_rectangle_sketch


def test_mesh_boolean_join_fallback_or_real():
    a = create_cube(size=2.0, name="A")
    b = create_cube(size=1.0, name="B")
    # Shift B so it overlaps
    b.vertices = [[v[0] + 1.0, v[1], v[2]] for v in b.vertices]
    result = mesh_boolean(a, b, "join", name="Union")
    assert isinstance(result, Mesh)
    assert len(result.vertices) > 0
    assert len(result.faces) > 0
    result.validate()


def test_mesh_boolean_cut_if_engine():
    a = create_cube(size=2.0, name="A")
    b = create_cylinder(radius=0.4, height=3.0, segments=8, name="Tool")
    try:
        result = mesh_boolean(a, b, "cut", name="Cut")
        assert isinstance(result, Mesh)
        assert len(result.faces) > 0
        result.validate()
    except BooleanError:
        pytest.skip("Boolean engine not available for cut")


def test_feature_history_join_operation():
    sk1 = create_rectangle_sketch(width=2.0, height=2.0, name="Base")
    sk2 = create_rectangle_sketch(width=1.0, height=1.0, name="Boss")
    hist = FeatureHistory(name="Test")
    e1 = ExtrudeFeature(sketch_id=sk1.id, distance=1.0, name="Base", operation="new")
    e2 = ExtrudeFeature(sketch_id=sk2.id, distance=1.0, name="Boss", operation="join",
                        start_offset=1.0)
    hist.add_extrude(e1)
    hist.add_extrude(e2)
    meshes = hist.recompute_meshes({sk1.id: sk1, sk2.id: sk2})
    assert e1.id in meshes
    assert e2.id in meshes
    # Second feature should be a result mesh (joined or fallback)
    assert isinstance(meshes[e2.id], Mesh)
    meshes[e2.id].validate()


def test_repair_mesh_preserves_valid_cube():
    from pymodeler.core.boolean import repair_mesh
    cube = create_cube(size=2.0, name="Solid")
    repaired = repair_mesh(cube)
    assert isinstance(repaired, Mesh)
    assert len(repaired.vertices) > 0
    assert len(repaired.faces) > 0
    repaired.validate()
    # Name preserved
    assert repaired.name == "Solid"


def test_mesh_boolean_with_repaired_inputs():
    a = create_cube(size=2.0, name="A")
    b = create_cube(size=1.0, name="B")
    b.vertices = [[v[0] + 0.8, v[1] + 0.2, v[2]] for v in b.vertices]
    result = mesh_boolean(a, b, "join", name="RepairedJoin")
    assert isinstance(result, Mesh)
    assert len(result.faces) > 0
    result.validate()
