"""Tests for transform gizmo interaction logic (headless-friendly)."""

import math
import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.core import Scene, SceneObject, create_cube, Transform
from pymodeler.render import ViewportWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_gizmo_mode_default(qapp):
    vp = ViewportWidget()
    assert vp.gizmo_mode == "translate"
    vp.close()


def test_gizmo_hit_and_drag_translate(qapp):
    vp = ViewportWidget()
    scene = Scene(name="Test")
    obj = SceneObject(name="Cube", mesh=create_cube())
    obj.transform.location = [1.0, 0.0, 0.0]
    scene.add_object(obj)
    scene.select(obj)
    vp.set_scene(scene)
    # Force a reasonable size for projection math
    vp.resize(800, 600)
    # The hit test should not crash even without a real GL context
    # (it uses camera math which is pure)
    axis = vp._hit_gizmo(400, 300)
    # May or may not hit depending on camera; just ensure no exception
    assert axis is None or axis in (0, 1, 2)
    # Simulate a drag start
    vp._gizmo_axis = 0
    vp._drag_start_mouse = type("P", (), {"x": lambda self: 400, "y": lambda self: 300})()
    vp._drag_start_transform = Transform(location=[1.0, 0.0, 0.0])
    vp.gizmo_mode = "translate"
    # Apply a synthetic drag
    class FakePos:
        def x(self): return 450
        def y(self): return 300
    vp._apply_gizmo_drag(FakePos())
    assert obj.transform.location[0] != 1.0  # moved along X (world or local identity)
    vp.close()


def test_gizmo_oriented_translate(qapp):
    """When object is rotated 90° around Y, local X axis points along world Z."""
    vp = ViewportWidget()
    scene = Scene(name="Test")
    obj = SceneObject(name="Cube", mesh=create_cube())
    obj.transform.location = [0.0, 0.0, 0.0]
    obj.transform.rotation = [0.0, math.pi / 2, 0.0]  # 90° Y
    scene.add_object(obj)
    scene.select(obj)
    vp.set_scene(scene)
    vp.resize(800, 600)

    # Local X should now point mostly along world +Z
    offsets = vp._local_axes(obj.transform, 1.0)
    local_x = offsets[0]
    assert abs(local_x[2]) > abs(local_x[0])  # more Z than X

    # Drag along local X should change world Z more than X
    vp._gizmo_axis = 0
    vp._drag_start_mouse = type("P", (), {"x": lambda self: 400, "y": lambda self: 300})()
    vp._drag_start_transform = Transform(
        location=[0.0, 0.0, 0.0],
        rotation=[0.0, math.pi / 2, 0.0],
    )
    vp.gizmo_mode = "translate"

    class FakePos:
        def x(self): return 450
        def y(self): return 300

    vp._apply_gizmo_drag(FakePos())
    # After rotation, movement on local X affects Z
    assert abs(obj.transform.location[2]) > abs(obj.transform.location[0])
    vp.close()


def test_gizmo_modes_switch(qapp):
    vp = ViewportWidget()
    assert vp.gizmo_mode == "translate"
    vp.gizmo_mode = "rotate"
    assert vp.gizmo_mode == "rotate"
    vp.gizmo_mode = "scale"
    assert vp.gizmo_mode == "scale"
    vp.close()
