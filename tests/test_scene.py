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
