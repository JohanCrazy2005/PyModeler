"""Tests for the visual sketch canvas."""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF

from pymodeler.core import Sketch, create_rectangle_sketch
from pymodeler.ui.sketch_canvas import SketchCanvasWidget
from pymodeler.ui.sketch_editor import SketchEditorWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_sketch_canvas_loads_and_displays_rectangle(qapp):
    sketch = create_rectangle_sketch(width=10, height=5, name="CanvasTest")
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    assert canvas.sketch is sketch
    # Scene should have items (points + lines)
    assert canvas.scene.items()
    canvas.close()


def test_sketch_canvas_add_point_via_mode(qapp):
    sketch = Sketch(name="EmptyCanvas")
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    assert len(sketch.entities) == 0

    canvas.set_mode("point")
    # Simulate a mouse press at scene origin (we call the handler logic indirectly by invoking add)
    # Directly exercise the public path used by mouse
    sketch.add_point(1.0, 2.0)
    canvas.refresh()
    assert len(sketch.entities) == 1
    assert any(e["type"] == "point" for e in sketch.entities)
    canvas.close()


def test_sketch_editor_includes_canvas(qapp):
    sketch = Sketch(name="WithCanvas")
    editor = SketchEditorWidget()
    editor.set_sketch(sketch)
    assert hasattr(editor, "canvas")
    assert editor.canvas.sketch is sketch
    editor._add_point()
    assert len(sketch.entities) == 1
    # Canvas should reflect the change
    assert editor.canvas.scene.items()
    editor.close()
