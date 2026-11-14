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
    restored = Scene.from_dict(data)
    assert restored.name == scene.name
    assert len(restored.objects) == 1
    assert restored.objects[0].mesh.name == "Cube"


def test_add_object():
    scene = Scene()
    mesh = create_cube()
    obj = SceneObject(name="Cube", mesh=mesh)
    scene.add_object(obj)
    scene.validate()
    assert len(scene.objects) == 1


def test_selection_basic():
    scene = Scene()
    mesh1 = create_cube(name="Cube1")
    mesh2 = create_cube(name="Cube2")
    obj1 = SceneObject(name="Cube1", mesh=mesh1)
    obj2 = SceneObject(name="Cube2", mesh=mesh2)
    scene.add_object(obj1)
    scene.add_object(obj2)

    assert not scene.is_selected(obj1)
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
