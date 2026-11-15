"""Tests for the sketch editor UI stub."""

import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.core import Sketch, create_rectangle_sketch
from pymodeler.ui.sketch_editor import SketchEditorWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_sketch_editor_loads_rectangle(qapp):
    sketch = create_rectangle_sketch(width=20, height=10, name="TestRect")
    editor = SketchEditorWidget()
    editor.set_sketch(sketch)
    assert editor.name_edit.text() == "TestRect"
    assert editor.entities_table.rowCount() == 8  # 4 points + 4 lines
    assert editor.constraints_table.rowCount() >= 6
    assert editor.dimensions_table.rowCount() == 2
    editor.close()


def test_sketch_editor_add_point_and_circle(qapp):
    sketch = Sketch(name="Empty")
    editor = SketchEditorWidget()
    editor.set_sketch(sketch)
    assert editor.entities_table.rowCount() == 0

    editor._add_point()
    assert len(sketch.entities) == 1
    assert sketch.entities[0]["type"] == "point"

    editor._add_circle()
    assert len(sketch.entities) == 2
    assert sketch.entities[1]["type"] == "circle"
    editor.close()


def test_sketch_editor_add_dimension(qapp):
    sketch = Sketch(name="WithLine")
    p1 = sketch.add_point(0, 0)
    p2 = sketch.add_point(10, 0)
    line = sketch.add_line(p1, p2)
    editor = SketchEditorWidget()
    editor.set_sketch(sketch)
    editor.dim_type.setCurrentText("length")
    editor.dim_value.setText("15")
    editor._add_dimension()
    assert len(sketch.dimensions) == 1
    assert sketch.dimensions[0]["type"] == "length"
    assert sketch.dimensions[0]["value"] == 15.0
    editor.close()
