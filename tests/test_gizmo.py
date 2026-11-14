"""Tests for transform gizmo interaction logic (headless-friendly)."""

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
    assert obj.transform.location[0] != 1.0  # moved along X
    vp.close()


def test_gizmo_modes_switch(qapp):
    vp = ViewportWidget()
    assert vp.gizmo_mode == "translate"
    vp.gizmo_mode = "rotate"
    assert vp.gizmo_mode == "rotate"
    vp.gizmo_mode = "scale"
    assert vp.gizmo_mode == "scale"
    vp.close()
