"""Tests for the command-pattern Undo/Redo stack."""

import pytest

from pymodeler.core import (
    Scene,
    SceneObject,
    Transform,
    create_cube,
    CommandStack,
    AddObjectCommand,
    RemoveObjectCommand,
    SetTransformCommand,
    ExtrudeMeshCommand,
    InsetMeshCommand,
)


def test_add_object_undo_redo():
    scene = Scene()
    mesh = create_cube()
    obj = SceneObject(name="Cube", mesh=mesh)
    stack = CommandStack()

    cmd = AddObjectCommand(scene, obj)
    stack.push(cmd)
    assert len(scene.objects) == 1
    assert stack.can_undo()
    assert not stack.can_redo()

    stack.undo()
    assert len(scene.objects) == 0
    assert not stack.can_undo()
    assert stack.can_redo()

    stack.redo()
    assert len(scene.objects) == 1
    assert scene.objects[0].name == "Cube"


def test_remove_object_undo_redo():
    scene = Scene()
    obj1 = SceneObject(name="A", mesh=create_cube())
    obj2 = SceneObject(name="B", mesh=create_cube())
    scene.add_object(obj1)
    scene.add_object(obj2)
    stack = CommandStack()

    cmd = RemoveObjectCommand(scene, obj1)
    stack.push(cmd)
    assert len(scene.objects) == 1
    assert scene.objects[0].name == "B"

    stack.undo()
    assert len(scene.objects) == 2
    assert scene.objects[0].name == "A"
    assert scene.objects[1].name == "B"

    stack.redo()
    assert len(scene.objects) == 1
    assert scene.objects[0].name == "B"


def test_set_transform_undo_redo():
    scene = Scene()
    obj = SceneObject(name="Cube", mesh=create_cube())
    scene.add_object(obj)
    stack = CommandStack()

    original = Transform(location=[0, 0, 0])
    assert obj.transform.location == [0.0, 0.0, 0.0]

    new_t = Transform(location=[1.0, 2.0, 3.0], rotation=[0.1, 0.2, 0.3], scale=[2, 2, 2])
    cmd = SetTransformCommand(obj, new_t)
    stack.push(cmd)

    assert obj.transform.location == [1.0, 2.0, 3.0]
    assert obj.transform.scale == [2, 2, 2]

    stack.undo()
    assert obj.transform.location == [0.0, 0.0, 0.0]
    assert obj.transform.scale == [1.0, 1.0, 1.0]

    stack.redo()
    assert obj.transform.location == [1.0, 2.0, 3.0]


def test_stack_limit_and_clear():
    scene = Scene()
    stack = CommandStack(limit=2)

    for i in range(4):
        obj = SceneObject(name=f"Obj{i}", mesh=create_cube())
        stack.push(AddObjectCommand(scene, obj))

    assert len(scene.objects) == 4
    assert len(stack._undo_stack) == 2  # limited

    stack.clear()
    assert not stack.can_undo()
    assert not stack.can_redo()


def test_selection_cleared_on_remove():
    scene = Scene()
    obj = SceneObject(name="Cube", mesh=create_cube())
    scene.add_object(obj)
    scene.select(obj)
    assert scene.is_selected(obj)

    stack = CommandStack()
    stack.push(RemoveObjectCommand(scene, obj))
    assert not scene.is_selected(obj)
    assert len(scene.objects) == 0

    stack.undo()
    assert len(scene.objects) == 1
    # Selection is not automatically restored (by design for now)
    assert not scene.is_selected(obj)


def test_extrude_mesh_command_undo_redo():
    scene = Scene()
    mesh = create_cube()
    obj = SceneObject(name="Cube", mesh=mesh)
    scene.add_object(obj)
    stack = CommandStack()

    orig_verts = len(obj.mesh.vertices)
    orig_faces = len(obj.mesh.faces)

    cmd = ExtrudeMeshCommand(obj, face_indices=None, direction=(0, 1, 0), distance=0.5)
    stack.push(cmd)

    assert len(obj.mesh.vertices) > orig_verts
    assert len(obj.mesh.faces) > orig_faces
    obj.mesh.validate()

    stack.undo()
    assert len(obj.mesh.vertices) == orig_verts
    assert len(obj.mesh.faces) == orig_faces
    obj.mesh.validate()

    stack.redo()
    assert len(obj.mesh.vertices) > orig_verts
    obj.mesh.validate()


def test_inset_mesh_command_undo_redo():
    scene = Scene()
    mesh = create_cube()
    obj = SceneObject(name="Cube", mesh=mesh)
    scene.add_object(obj)
    stack = CommandStack()

    orig_verts = len(obj.mesh.vertices)
    orig_faces = len(obj.mesh.faces)

    cmd = InsetMeshCommand(obj, thickness=0.25, depth=0.0)
    stack.push(cmd)

    assert len(obj.mesh.vertices) > orig_verts
    assert len(obj.mesh.faces) > orig_faces
    obj.mesh.validate()

    stack.undo()
    assert len(obj.mesh.vertices) == orig_verts
    assert len(obj.mesh.faces) == orig_faces
    obj.mesh.validate()

    stack.redo()
    assert len(obj.mesh.vertices) > orig_verts
    obj.mesh.validate()
