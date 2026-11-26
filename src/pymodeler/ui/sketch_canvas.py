"""Interactive sketch canvas widget (QGraphicsView).

Visualizes sketch entities (points, lines, circles, arcs) and supports basic
mouse drawing modes with simple snapping. Emits sketch_changed when the model
is modified via the canvas.
"""

from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPathItem, QWidget

from pymodeler.core.sketch import Sketch


class SketchCanvasWidget(QGraphicsView):
    """Canvas that holds a Sketch, draws its entities, and supports drawing modes."""

    sketch_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.sketch: Optional[Sketch] = None
        self.setMinimumHeight(200)
        self.setRenderHint(self.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Interaction state
        self.mode: str = "select"  # select, point, line, circle, rectangle, arc
        self.selected_id: Optional[str] = None
        self._start_point: Optional[str] = None
        self._preview_item = None
        self._last_mouse_pos: Optional[QPointF] = None

        # Visual styles
        self._point_radius = 3.0
        self._pen_normal = QPen(QColor(40, 40, 40), 1.5)
        self._pen_construction = QPen(QColor(150, 150, 150), 1.0, Qt.PenStyle.DashLine)
        self._pen_selected = QPen(QColor(0, 120, 215), 2.5)
        self._brush_point = QBrush(QColor(40, 40, 40))
        self._brush_selected = QBrush(QColor(0, 120, 215))

    def set_sketch(self, sketch: Optional[Sketch]) -> None:
        self.sketch = sketch
        self.selected_id = None
        self._start_point = None
        self.refresh()

    def set_mode(self, mode: str) -> None:
        """Set drawing / interaction mode."""
        self.mode = mode
        self._start_point = None
        self._clear_preview()
        if mode == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def refresh(self) -> None:
        """Rebuild scene items from the current sketch."""
        self.scene.clear()
        self._preview_item = None
        if self.sketch is None:
            return

        # Build point lookup
        points = {}
        for ent in self.sketch.entities:
            if ent.get("type") == "point":
                points[ent["id"]] = (float(ent["x"]), float(ent["y"]))

        for ent in self.sketch.entities:
            et = ent.get("type")
            eid = ent.get("id")
            construction = ent.get("construction", False)
            is_selected = eid == self.selected_id
            pen = self._pen_selected if is_selected else (self._pen_construction if construction else self._pen_normal)

            if et == "point":
                x, y = float(ent["x"]), float(ent["y"])
                item = self.scene.addEllipse(
                    x - self._point_radius, y - self._point_radius,
                    self._point_radius * 2, self._point_radius * 2,
                    pen,
                    self._brush_selected if is_selected else self._brush_point,
                )
                item.setData(0, eid)
                item.setZValue(10)

            elif et == "line":
                sp = points.get(ent.get("start_point"))
                ep = points.get(ent.get("end_point"))
                if sp and ep:
                    item = self.scene.addLine(sp[0], sp[1], ep[0], ep[1], pen)
                    item.setData(0, eid)
                    item.setZValue(5)

            elif et == "circle":
                c = points.get(ent.get("center"))
                if c:
                    r = float(ent.get("radius", 1.0))
                    item = self.scene.addEllipse(c[0] - r, c[1] - r, r * 2, r * 2, pen)
                    item.setData(0, eid)
                    item.setZValue(4)

            elif et == "arc":
                c = points.get(ent.get("center"))
                if c:
                    r = float(ent.get("radius", 1.0))
                    sa = float(ent.get("start_angle", 0.0))
                    ea = float(ent.get("end_angle", 90.0))
                    path = QPainterPath()
                    path.arcMoveTo(c[0] - r, c[1] - r, r * 2, r * 2, sa)
                    path.arcTo(c[0] - r, c[1] - r, r * 2, r * 2, sa, ea - sa)
                    item = self.scene.addPath(path, pen)
                    item.setData(0, eid)
                    item.setZValue(4)

        # Fit if content exists
        if self.scene.items():
            self.fitInView(self.scene.itemsBoundingRect().adjusted(-10, -10, 10, 10), Qt.AspectRatioMode.KeepAspectRatio)

    def _clear_preview(self) -> None:
        if self._preview_item is not None:
            self.scene.removeItem(self._preview_item)
            self._preview_item = None

    def _snap(self, pos: QPointF, tol: float = 8.0) -> QPointF:
        """Snap to nearest point if within tolerance (in scene units after transform)."""
        if self.sketch is None:
            return pos
        scene_pos = self.mapToScene(pos.toPoint())
        best = scene_pos
        best_d = tol
        for ent in self.sketch.entities:
            if ent.get("type") == "point":
                px, py = float(ent["x"]), float(ent["y"])
                d = math.hypot(scene_pos.x() - px, scene_pos.y() - py)
                if d < best_d:
                    best_d = d
                    best = QPointF(px, py)
        return best

    def mousePressEvent(self, event):
        if self.sketch is None or event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        scene_pos = self.mapToScene(event.position().toPoint())
        snapped = self._snap(event.position())

        if self.mode == "point":
            self.sketch.add_point(snapped.x(), snapped.y())
            self.sketch_changed.emit()
            self.refresh()
            return

        if self.mode == "line":
            if self._start_point is None:
                pid = self._find_or_add_point(snapped)
                self._start_point = pid
            else:
                pid = self._find_or_add_point(snapped)
                if pid != self._start_point:
                    self.sketch.add_line(self._start_point, pid)
                    self.sketch_changed.emit()
                self._start_point = None
                self._clear_preview()
                self.refresh()
            return

        if self.mode == "circle":
            if self._start_point is None:
                pid = self._find_or_add_point(snapped)
                self._start_point = pid
            else:
                center = self.sketch.get_entity(self._start_point)
                if center:
                    cx, cy = float(center["x"]), float(center["y"])
                    r = math.hypot(snapped.x() - cx, snapped.y() - cy)
                    if r > 0.1:
                        self.sketch.add_circle(self._start_point, r)
                        self.sketch_changed.emit()
                self._start_point = None
                self._clear_preview()
                self.refresh()
            return

        if self.mode == "rectangle":
            if self._start_point is None:
                pid = self._find_or_add_point(snapped)
                self._start_point = pid
            else:
                start_ent = self.sketch.get_entity(self._start_point)
                if start_ent:
                    x1, y1 = float(start_ent["x"]), float(start_ent["y"])
                    x2, y2 = snapped.x(), snapped.y()
                    if abs(x2 - x1) > 0.1 and abs(y2 - y1) > 0.1:
                        p_br = self.sketch.add_point(x2, y1)
                        p_tr = self.sketch.add_point(x2, y2)
                        p_tl = self.sketch.add_point(x1, y2)
                        self.sketch.add_line(self._start_point, p_br)
                        self.sketch.add_line(p_br, p_tr)
                        self.sketch.add_line(p_tr, p_tl)
                        self.sketch.add_line(p_tl, self._start_point)
                        self.sketch_changed.emit()
                self._start_point = None
                self._clear_preview()
                self.refresh()
            return

        if self.mode == "select":
            item = self.scene.itemAt(scene_pos, self.transform())
            if item is not None:
                eid = item.data(0)
                if eid:
                    self.selected_id = eid
                    self.refresh()
                    return
            self.selected_id = None
            self.refresh()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.sketch is None or self._start_point is None:
            return super().mouseMoveEvent(event)

        snapped = self._snap(event.position())
        self._clear_preview()

        start_ent = self.sketch.get_entity(self._start_point)
        if not start_ent:
            return

        sx, sy = float(start_ent["x"]), float(start_ent["y"])
        pen = QPen(QColor(0, 150, 255), 1.0, Qt.PenStyle.DashLine)

        if self.mode == "line":
            self._preview_item = self.scene.addLine(sx, sy, snapped.x(), snapped.y(), pen)
        elif self.mode == "circle":
            r = math.hypot(snapped.x() - sx, snapped.y() - sy)
            if r > 0:
                self._preview_item = self.scene.addEllipse(sx - r, sy - r, r * 2, r * 2, pen)
        elif self.mode == "rectangle":
            x1, y1 = sx, sy
            x2, y2 = snapped.x(), snapped.y()
            path = QPainterPath()
            path.addRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            self._preview_item = self.scene.addPath(path, pen)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def _find_or_add_point(self, pos: QPointF, tol: float = 0.5) -> str:
        """Return existing point id near pos or create a new one."""
        if self.sketch is None:
            raise RuntimeError("No sketch")
        for ent in self.sketch.entities:
            if ent.get("type") == "point":
                if math.hypot(float(ent["x"]) - pos.x(), float(ent["y"]) - pos.y()) < tol:
                    return ent["id"]
        return self.sketch.add_point(pos.x(), pos.y())

    def wheelEvent(self, event):
        """Simple zoom with mouse wheel."""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
