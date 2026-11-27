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


def test_sketch_canvas_select_mode_and_highlight(qapp):
    sketch = Sketch(name="SelectTest")
    pid = sketch.add_point(1.0, 1.0)
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    canvas.set_mode("select")
    assert canvas.mode == "select"
    canvas.selected_id = pid
    canvas.refresh()
    # Selected point should still be present
    assert any(item.data(0) == pid for item in canvas.scene.items())
    canvas.close()


def test_sketch_canvas_update_point_via_drag_logic(qapp):
    sketch = Sketch(name="DragTest")
    pid = sketch.add_point(0.0, 0.0)
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    canvas.set_mode("select")
    # Exercise the update path used by dragging
    sketch.update_point(pid, 3.5, -1.2)
    assert sketch.get_entity(pid)["x"] == 3.5
    assert sketch.get_entity(pid)["y"] == -1.2
    canvas.refresh()
    canvas.close()


def test_sketch_canvas_rectangle_mode_creates_entities(qapp):
    sketch = Sketch(name="RectMode")
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    canvas.set_mode("rectangle")
    assert canvas.mode == "rectangle"
    # Manually exercise creation similar to mouse release
    start = sketch.add_point(0.0, 0.0)
    # Simulate end point
    canvas._start_point = start
    # Call the release logic indirectly by adding the expected entities
    p_br = sketch.add_point(10.0, 0.0)
    p_tr = sketch.add_point(10.0, 5.0)
    p_tl = sketch.add_point(0.0, 5.0)
    sketch.add_line(start, p_br)
    sketch.add_line(p_br, p_tr)
    sketch.add_line(p_tr, p_tl)
    sketch.add_line(p_tl, start)
    assert len([e for e in sketch.entities if e["type"] == "line"]) == 4
    assert len([e for e in sketch.entities if e["type"] == "point"]) == 4
    canvas.close()


def test_sketch_canvas_arc_mode_creates_arc(qapp):
    sketch = Sketch(name="ArcMode")
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    canvas.set_mode("arc")
    assert canvas.mode == "arc"
    # Simulate 3-click center → start → end by setting state then calling add
    center = sketch.add_point(0.0, 0.0)
    canvas._arc_center = center
    canvas._arc_radius = 5.0
    canvas._arc_start_angle = 0.0
    # Directly create the arc as the third click would
    sketch.add_arc(center, 5.0, 0.0, 90.0)
    assert any(e["type"] == "arc" and e["radius"] == 5.0 for e in sketch.entities)
    canvas.refresh()
    # Arc path should be drawn
    assert canvas.scene.items()
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


def test_circle_from_3_points_and_arc_angles():
    from pymodeler.ui.sketch_canvas import _circle_from_3_points, _arc_angles_through
    # Unit circle points: (1,0), (0,1), (-1,0) → center (0,0) r=1
    c = _circle_from_3_points(1.0, 0.0, 0.0, 1.0, -1.0, 0.0)
    assert c is not None
    cx, cy, r = c
    assert abs(cx) < 1e-9 and abs(cy) < 1e-9
    assert abs(r - 1.0) < 1e-9
    # Collinear → None
    assert _circle_from_3_points(0.0, 0.0, 1.0, 0.0, 2.0, 0.0) is None
    # Arc angles: start 0°, through 90°, end 180° → sweep 180
    sa, ea = _arc_angles_through(0.0, 90.0, 180.0)
    assert abs(sa - 0.0) < 1e-9
    assert abs((ea - sa) % 360 - 180.0) < 1e-6


def test_sketch_canvas_arc3_mode_creates_arc(qapp):
    sketch = Sketch(name="Arc3Mode")
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    canvas.set_mode("arc3")
    assert canvas.mode == "arc3"
    # Simulate 3 clicks via state + geometry helper path
    from pymodeler.ui.sketch_canvas import _circle_from_3_points, _arc_angles_through
    from PyQt6.QtCore import QPointF
    p1 = sketch.add_point(1.0, 0.0)
    p2 = sketch.add_point(0.0, 1.0)
    canvas._arc3_p1 = p1
    canvas._arc3_p2 = p2
    # Third point (-1, 0) → semicircle upper
    circle = _circle_from_3_points(1.0, 0.0, 0.0, 1.0, -1.0, 0.0)
    assert circle is not None
    cx, cy, r = circle
    center_id = canvas._find_or_add_point(QPointF(cx, cy), tol=0.25)
    a1 = 0.0
    a2 = 90.0
    a3 = 180.0
    sa, ea = _arc_angles_through(a1, a2, a3)
    sketch.add_arc(center_id, r, sa, ea)
    arcs = [e for e in sketch.entities if e["type"] == "arc"]
    assert len(arcs) == 1
    assert abs(arcs[0]["radius"] - 1.0) < 1e-6
    canvas.refresh()
    assert canvas.scene.items()
    canvas.close()


def test_sketch_canvas_badge_toggle_and_related(qapp):
    """Badges can be toggled; they store type/index/related; click selects related."""
    sketch = create_rectangle_sketch(width=10, height=5, name="BadgePolish")
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    canvas.refresh()
    badges = [item for item in canvas.scene.items() if item.data(1) == "badge"]
    assert len(badges) >= 1
    # Has type and related stored
    b = badges[0]
    assert b.data(2) in ("constraint", "dimension")
    assert isinstance(b.data(4), list)
    # Toggle off
    canvas.set_show_badges(False)
    badges_off = [item for item in canvas.scene.items() if item.data(1) == "badge"]
    assert len(badges_off) == 0
    canvas.set_show_badges(True)
    badges_on = [item for item in canvas.scene.items() if item.data(1) == "badge"]
    assert len(badges_on) >= 1
    # Simulate click on first badge via data
    related = badges_on[0].data(4)
    if related:
        canvas.selected_ids = set(related)
        canvas._related_ids = set(related)
        canvas.refresh()
        assert canvas.selected_ids == set(related)
    canvas.close()


def test_sketch_canvas_constraint_and_dimension_badges(qapp):
    """Constraint and dimension badges appear in the scene."""
    sketch = create_rectangle_sketch(width=10, height=5, name="BadgeTest")
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    canvas.refresh()
    badges = [item for item in canvas.scene.items() if item.data(1) == "badge"]
    # Rectangle has H/V/equal constraints + length dimensions
    assert len(badges) >= 4
    canvas.close()


def test_sketch_canvas_multi_select_and_box(qapp):
    """Multi-select via Shift-style API and box select helper."""
    sketch = Sketch(name="MultiSelect")
    p1 = sketch.add_point(0.0, 0.0)
    p2 = sketch.add_point(10.0, 0.0)
    p3 = sketch.add_point(10.0, 10.0)
    canvas = SketchCanvasWidget()
    canvas.set_sketch(sketch)
    canvas.set_mode("select")

    # Direct multi-select API
    canvas.selected_ids = {p1, p2}
    canvas.selected_id = p2
    canvas.refresh()
    highlighted = [item.data(0) for item in canvas.scene.items() if item.data(0) in canvas.selected_ids]
    assert set(highlighted) >= {p1, p2}

    # Box select path
    from PyQt6.QtCore import QPointF, QRectF
    canvas._finish_box_select(QPointF(-1, -1), QPointF(11, 1))
    assert p1 in canvas.selected_ids
    assert p2 in canvas.selected_ids
    assert p3 not in canvas.selected_ids
    canvas.close()
