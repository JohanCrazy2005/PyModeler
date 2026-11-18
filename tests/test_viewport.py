"""Tests for the OpenGL viewport widget (graceful under offscreen)."""

import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.core import Scene, SceneObject, create_cube
from pymodeler.render import ViewportWidget
from pymodeler.render.viewport import extract_unique_edges
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


def test_wireframe_toggle_and_frame(qapp):
    vp = ViewportWidget()
    assert vp.shading_mode == "solid"
    vp.toggle_wireframe()
    assert vp.shading_mode == "wireframe"
    vp.toggle_wireframe()
    assert vp.shading_mode == "solid_wire"
    vp.set_shading_mode("solid")
    assert vp.shading_mode == "solid"
    scene = Scene(name="Test")
    obj = SceneObject(name="Cube", mesh=create_cube())
    scene.add_object(obj)
    vp.set_scene(scene)
    # Frame methods should not crash even without GL
    vp.frame_all()
    vp.frame_selected()
    assert vp.camera.distance > 0
    vp.close()


def test_standard_views_and_ortho(qapp):
    vp = ViewportWidget()
    vp.set_standard_view("front")
    assert abs(vp.camera.azimuth) < 1.0
    assert abs(vp.camera.elevation) < 1.0
    vp.set_standard_view("top")
    assert abs(vp.camera.elevation - 89.0) < 1.0
    assert not vp.camera.orthographic
    vp.toggle_orthographic()
    assert vp.camera.orthographic
    vp.toggle_orthographic()
    assert not vp.camera.orthographic
    vp.close()


def test_extract_unique_edges_cube():
    mesh = create_cube()
    edges = extract_unique_edges(mesh.faces)
    # A cube has 12 unique edges
    assert len(edges) == 12
    # All edges are unique pairs of valid indices
    for a, b in edges:
        assert 0 <= a < 8 and 0 <= b < 8
        assert a < b


def test_selection_outline_and_gizmo_draw_safe(qapp):
    """Drawing methods must early-return cleanly when no GL context is available."""
    vp = ViewportWidget()
    scene = Scene(name="Test")
    obj = SceneObject(name="Cube", mesh=create_cube())
    scene.add_object(obj)
    scene.select(obj)
    vp.set_scene(scene)
    # Force paint path (no-op without GL)
    vp.paintGL()
    # Explicit calls should not raise
    mvp = vp.camera.projection_matrix(1.0) @ vp.camera.view_matrix()
    vp._draw_selection_outline(obj, mvp)
    vp._draw_gizmo_axes(obj, mvp)
    assert vp.show_selection_outline is True
    vp.close()
