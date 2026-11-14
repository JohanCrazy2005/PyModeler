"""Basic tests that the application can start (headless-friendly)."""

import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_creates(qapp):
    window = MainWindow()
    assert window.windowTitle() == "PyModeler"
    assert window.scene is not None
    assert len(window.scene.objects) == 0
    window.close()


def test_add_cube_from_window(qapp):
    window = MainWindow()
    window.add_cube()
    assert len(window.scene.objects) == 1
    assert window.scene.objects[0].name == "Cube"
    window.scene.validate()
    window.close()


def test_extrude_selected_from_window(qapp):
    window = MainWindow()
    window.add_cube()
    obj = window.scene.objects[0]
    orig_verts = len(obj.mesh.vertices)
    orig_faces = len(obj.mesh.faces)

    window.extrude_selected()

    assert len(obj.mesh.vertices) > orig_verts
    assert len(obj.mesh.faces) > orig_faces
    obj.mesh.validate()
    assert window.history.can_undo()

    window.undo()
    assert len(obj.mesh.vertices) == orig_verts
    assert len(obj.mesh.faces) == orig_faces
    obj.mesh.validate()

    window.close()
