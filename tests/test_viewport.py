"""Tests for the OpenGL viewport widget (graceful under offscreen)."""

import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.core import Scene, SceneObject, create_cube
from pymodeler.render import ViewportWidget
from pymodeler.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_viewport_widget_creates(qapp):
    vp = ViewportWidget()
    assert vp is not None
    assert vp.camera is not None
    assert vp.camera.distance > 0
    vp.close()


def test_viewport_accepts_scene(qapp):
    vp = ViewportWidget()
    scene = Scene(name="Test")
    obj = SceneObject(name="Cube", mesh=create_cube())
    scene.add_object(obj)
    vp.set_scene(scene)
    assert vp._scene is scene
    vp.close()


def test_main_window_has_viewport(qapp):
    window = MainWindow()
    assert hasattr(window, "viewport")
    assert isinstance(window.viewport, ViewportWidget)
    window.add_cube()
    assert len(window.scene.objects) == 1
    # set_scene should have been called
    assert window.viewport._scene is window.scene
    window.close()


def test_camera_orbit_and_zoom(qapp):
    vp = ViewportWidget()
    cam = vp.camera
    old_az = cam.azimuth
    cam.orbit(10.0, 5.0)
    assert cam.azimuth == old_az + 10.0
    old_dist = cam.distance
    cam.zoom(120)  # positive wheel-ish
    assert cam.distance != old_dist
    vp.close()
