"""Tests for Scene and SceneObject."""

import pytest

from pymodeler.core import Scene, SceneObject, create_cube, SceneValidationError


def test_scene_with_cube():
    mesh = create_cube()
    obj = SceneObject(name="MyCube", mesh=mesh)
    scene = Scene(name="Test", objects=[obj])
    scene.validate()
    assert len(scene.objects) == 1
    assert scene.objects[0].name == "MyCube"


def test_scene_roundtrip():
    mesh = create_cube(name="Cube")
    obj = SceneObject(name="Cube", mesh=mesh)
    scene = Scene(objects=[obj])
    data = scene.to_dict()
    scene2 = Scene.from_dict(data)
    assert scene2.name == scene.name
    assert len(scene2.objects) == 1
    assert scene2.objects[0].name == "Cube"


def test_add_object():
    scene = Scene()
    obj = SceneObject(name="A", mesh=create_cube())
    scene.add_object(obj)
    assert len(scene.objects) == 1
    assert scene.get_object("A") is obj


def test_selection_basic():
    scene = Scene()
    obj1 = SceneObject(name="Cube1", mesh=create_cube())
    obj2 = SceneObject(name="Cube2", mesh=create_cube())
    scene.add_object(obj1)
    scene.add_object(obj2)
    scene.select(obj1)
    assert scene.is_selected(obj1)
    assert not scene.is_selected(obj2)
    assert len(scene.selected_objects()) == 1
    assert scene.selected_objects()[0].name == "Cube1"

    scene.select(obj2, clear=False)
    assert scene.is_selected(obj1)
    assert scene.is_selected(obj2)
    assert len(scene.selected_objects()) == 2

    scene.deselect(obj1)
    assert not scene.is_selected(obj1)
    assert scene.is_selected("Cube2")

    scene.clear_selection()
    assert len(scene.selected_objects()) == 0
    assert not scene.is_selected(obj2)


def test_selection_by_name():
    scene = Scene()
    obj = SceneObject(name="MyCube", mesh=create_cube())
    scene.add_object(obj)
    scene.select("MyCube")
    assert scene.is_selected("MyCube")
    assert scene.get_object("MyCube") is obj
    scene.select("NonExistent")  # should be no-op
    assert not scene.is_selected("NonExistent")
    assert len(scene.selected_names()) == 1


def test_transform_identity_matrix():
    import numpy as np
    from pymodeler.core import Transform

    t = Transform()
    m = t.matrix()
    assert m.shape == (4, 4)
    np.testing.assert_allclose(m, np.eye(4), atol=1e-6)


def test_transform_translation_only():
    import numpy as np
    from pymodeler.core import Transform

    t = Transform(location=[10.0, 20.0, 30.0])
    pts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=np.float32)
    world = t.transform_points(pts)
    expected = np.array([[10.0, 20.0, 30.0], [11.0, 20.0, 30.0]], dtype=np.float32)
    np.testing.assert_allclose(world, expected, atol=1e-5)


def test_transform_scale_only():
    import numpy as np
    from pymodeler.core import Transform

    t = Transform(scale=[2.0, 3.0, 4.0])
    pts = np.array([[1.0, 1.0, 1.0]], dtype=np.float32)
    world = t.transform_points(pts)
    np.testing.assert_allclose(world[0], [2.0, 3.0, 4.0], atol=1e-5)


def test_transform_rotation_90_y():
    import numpy as np
    from pymodeler.core import Transform
    import math

    # 90 deg about Y: (1,0,0) -> (0,0,-1)
    t = Transform(rotation=[0.0, math.pi / 2, 0.0])
    pts = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
    world = t.transform_points(pts)
    np.testing.assert_allclose(world[0], [0.0, 0.0, -1.0], atol=1e-5)


def test_full_transform_applied_to_world_vertices():
    """Core test for NEXT_STEPS item: full transform (scale+rot+loc) on vertices."""
    import numpy as np
    import math
    from pymodeler.core import Transform, SceneObject, create_cube

    # Scale 2x, rotate 90° about Y, translate (5,0,0)
    t = Transform(
        location=[5.0, 0.0, 0.0],
        rotation=[0.0, math.pi / 2, 0.0],
        scale=[2.0, 2.0, 2.0],
    )
    # Local point (1,0,0) -> scale (2,0,0) -> rotY90 (0,0,-2) -> +loc (5,0,-2)
    local = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
    world = t.transform_points(local)
    np.testing.assert_allclose(world[0], [5.0, 0.0, -2.0], atol=1e-5)

    # Also works on a real mesh
    mesh = create_cube()
    obj = SceneObject(name="ScaledRotated", mesh=mesh, transform=t)
    verts = np.array(obj.mesh.vertices, dtype=np.float32)
    world_verts = obj.transform.transform_points(verts)
    assert world_verts.shape == verts.shape
    # Centroid should be near the translation (cube centered at origin)
    centroid = world_verts.mean(axis=0)
    np.testing.assert_allclose(centroid, [5.0, 0.0, 0.0], atol=0.1)
