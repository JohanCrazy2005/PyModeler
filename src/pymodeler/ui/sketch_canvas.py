"""Interactive sketch canvas widget (QGraphicsView).

Visualizes sketch entities (points, lines, circles, arcs) and supports basic
mouse drawing modes with simple snapping. Emits sketch_changed when the model
is modified via the canvas. Now draws dimension labels, snaps to midpoints,
and supports full 3-click arc creation (center → start/radius → end angle)
plus 3-point arc mode (start → through → end).
"""

from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont, QPainter
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget

from pymodeler.core.sketch import Sketch


def _circle_from_3_points(
    x1: float, y1: float, x2: float, y2: float, x3: float, y3: float
) -> Optional[tuple[float, float, float]]:
    """Return (cx, cy, r) for the unique circle through three non-collinear points, else None."""
    d = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        return None
    ux = (
        (x1 * x1 + y1 * y1) * (y2 - y3)
        + (x2 * x2 + y2 * y2) * (y3 - y1)
        + (x3 * x3 + y3 * y3) * (y1 - y2)
    ) / d
    uy = (
        (x1 * x1 + y1 * y1) * (x3 - x2)
        + (x2 * x2 + y2 * y2) * (x1 - x3)
        + (x3 * x3 + y3 * y3) * (x2 - x1)
    ) / d
    r = math.hypot(x1 - ux, y1 - uy)
    if r < 1e-9:
        return None
    return (ux, uy, r)


def _arc_angles_through(a_start: float, a_through: float, a_end: float) -> tuple[float, float]:
    """Return (start_angle, end_angle) such that CCW arc from start passes through 'through' then end.

    Angles in degrees. Result end is start + positive sweep in (0, 360].
    """
    def norm(a: float) -> float:
        return a % 360.0

    s = norm(a_start)
    t = norm(a_through)
    e = norm(a_end)
    dt = (t - s) % 360.0
    de = (e - s) % 360.0
    if dt < 1e-9:
        dt = 0.0
    if de < 1e-9:
        de = 360.0
    if dt <= de + 1e-9:
        return (s, s + de if de > 0 else s + 360.0)
    sweep = dt + ((e - t) % 360.0)
    if sweep < 1e-9:
        sweep = 360.0
    if sweep > 360.0 + 1e-9:
        sweep = sweep % 360.0
        if sweep < 1e-9:
            sweep = 360.0
    return (s, s + sweep)


class SketchCanvasWidget(QGraphicsView):
    """Canvas that holds a Sketch, draws its entities, and supports drawing modes."""

    sketch_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.sketch: Optional[Sketch] = None
        self.setMinimumHeight(200)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Interaction state
        self.mode: str = "select"  # select, point, line, circle, rectangle, arc, arc3
        self.selected_id: Optional[str] = None
        self._start_point: Optional[str] = None
        self._preview_item = None
        self._last_mouse_pos: Optional[QPointF] = None
        # Arc mode multi-click state (center-radius)
        self._arc_center: Optional[str] = None
        self._arc_radius: Optional[float] = None
        self._arc_start_angle: Optional[float] = None
        # 3-point arc state (start → through → end)
        self._arc3_p1: Optional[str] = None
        self._arc3_p2: Optional[str] = None

        # Visual styles
        self._point_radius = 3.0
        self._pen_normal = QPen(QColor(40, 40, 40), 1.5)
        self._pen_construction = QPen(QColor(150, 150, 150), 1.0, Qt.PenStyle.DashLine)
        self._pen_selected = QPen(QColor(0, 120, 215), 2.5)
        self._brush_point = QBrush(QColor(40, 40, 40))
        self._brush_selected = QBrush(QColor(0, 120, 215))
        self._dim_font = QFont("Arial", 8)

    def set_sketch(self, sketch: Optional[Sketch]) -> None:
        self.sketch = sketch
        self.selected_id = None
        self._start_point = None
        self._reset_arc_state()
        self.refresh()

    def set_mode(self, mode: str) -> None:
        """Set drawing / interaction mode."""
        self.mode = mode
        self._start_point = None
        self._reset_arc_state()
        self._clear_preview()
        if mode == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def _reset_arc_state(self) -> None:
        self._arc_center = None
        self._arc_radius = None
        self._arc_start_angle = None
        self._arc3_p1 = None
        self._arc3_p2 = None
