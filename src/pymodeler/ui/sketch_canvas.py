"""Visual 2D sketch canvas using QGraphicsView.

Supports mouse drawing of points, lines, and circles with basic point snapping.
Syncs with the Sketch data model.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter
from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)

from pymodeler.core import Sketch


class SketchCanvasWidget(QWidget):
    """Interactive 2D canvas for sketching.

    Modes: point, line, circle.
    Basic snapping to existing points (within SNAP_DISTANCE scene units).
    """

    sketch_changed = pyqtSignal()

    SNAP_DISTANCE = 0.5  # scene units

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.sketch: Optional[Sketch] = None
        self.mode = "point"
        self._start_point: Optional[str] = None
        self._preview_item = None
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        self.point_btn = QPushButton("Point")
        self.point_btn.setCheckable(True)
        self.point_btn.setChecked(True)
        self.point_btn.clicked.connect(lambda: self.set_mode("point"))
        toolbar.addWidget(self.point_btn)

        self.line_btn = QPushButton("Line")
        self.line_btn.setCheckable(True)
        self.line_btn.clicked.connect(lambda: self.set_mode("line"))
        toolbar.addWidget(self.line_btn)

        self.circle_btn = QPushButton("Circle")
        self.circle_btn.setCheckable(True)
        self.circle_btn.clicked.connect(lambda: self.set_mode("circle"))
        toolbar.addWidget(self.circle_btn)

        toolbar.addStretch()
        toolbar.addWidget(QLabel("Snap to points enabled"))
        layout.addLayout(toolbar)

        # Graphics view
        self.scene = QGraphicsScene(-100, -100, 200, 200)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.mousePressEvent = self._on_mouse_press
        self.view.mouseMoveEvent = self._on_mouse_move
        self.view.mouseReleaseEvent = self._on_mouse_release
        layout.addWidget(self.view)

        self.setEnabled(False)

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.point_btn.setChecked(mode == "point")
        self.line_btn.setChecked(mode == "line")
        self.circle_btn.setChecked(mode == "circle")
        self._clear_preview()
        self._start_point = None

    def set_sketch(self, sketch: Optional[Sketch]) -> None:
        self.sketch = sketch
        self.setEnabled(sketch is not None)
        self.refresh()

    def refresh(self) -> None:
        if self._updating or self.sketch is None:
            return
        self._updating = True
        try:
            self.scene.clear()
            self._preview_item = None

            # Draw points
            point_items: dict[str, QGraphicsEllipseItem] = {}
            for ent in self.sketch.entities:
                if ent["type"] == "point":
                    x, y = float(ent["x"]), float(ent["y"])
                    r = 0.15
                    item = self.scene.addEllipse(x - r, -y - r, 2 * r, 2 * r)
                    item.setBrush(QBrush(QColor(80, 140, 255)))
                    item.setPen(QPen(QColor(40, 80, 200), 0.05))
                    item.setData(0, ent["id"])
                    point_items[ent["id"]] = item

            # Draw lines
            for ent in self.sketch.entities:
                if ent["type"] == "line":
                    start = self.sketch.get_entity(ent["start_point"])
                    end = self.sketch.get_entity(ent["end_point"])
                    if start and end and start["type"] == "point" and end["type"] == "point":
                        x1, y1 = float(start["x"]), float(start["y"])
                        x2, y2 = float(end["x"]), float(end["y"])
                        line = self.scene.addLine(x1, -y1, x2, -y2)
                        line.setPen(QPen(QColor(60, 60, 60), 0.08))
                        line.setData(0, ent["id"])

            # Draw circles
            for ent in self.sketch.entities:
                if ent["type"] == "circle":
                    center = self.sketch.get_entity(ent["center"])
                    if center and center["type"] == "point":
                        cx, cy = float(center["x"]), float(center["y"])
                        rad = float(ent["radius"])
                        circle = self.scene.addEllipse(cx - rad, -cy - rad, 2 * rad, 2 * rad)
                        circle.setPen(QPen(QColor(60, 60, 60), 0.08))
                        circle.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                        circle.setData(0, ent["id"])

            # Fit view if content exists
            if self.sketch.entities:
                self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-5, -5, 5, 5), Qt.AspectRatioMode.KeepAspectRatio)
        finally:
            self._updating = False

    def _snap_to_point(self, scene_pos: QPointF) -> tuple[float, float, Optional[str]]:
        """Return (x, y, point_id) snapped to nearest existing point if within SNAP_DISTANCE."""
        if self.sketch is None:
            return scene_pos.x(), -scene_pos.y(), None
        x, y = scene_pos.x(), -scene_pos.y()
        best_id = None
        best_dist = self.SNAP_DISTANCE
        for ent in self.sketch.entities:
            if ent["type"] == "point":
                dx = float(ent["x"]) - x
                dy = float(ent["y"]) - y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_id = ent["id"]
                    x, y = float(ent["x"]), float(ent["y"])
        return x, y, best_id

    def _clear_preview(self) -> None:
        if self._preview_item is not None:
            self.scene.removeItem(self._preview_item)
            self._preview_item = None

    def _on_mouse_press(self, event) -> None:
        if self.sketch is None or event.button() != Qt.MouseButton.LeftButton:
            return super(QGraphicsView, self.view).mousePressEvent(event)
        scene_pos = self.view.mapToScene(event.pos())
        x, y, snapped_id = self._snap_to_point(scene_pos)

        if self.mode == "point":
            self.sketch.add_point(x, y)
            self.refresh()
            self.sketch_changed.emit()
        elif self.mode in ("line", "circle"):
            if snapped_id:
                self._start_point = snapped_id
            else:
                self._start_point = self.sketch.add_point(x, y)
                self.refresh()
            self._clear_preview()

    def _on_mouse_move(self, event) -> None:
        if self.sketch is None or self._start_point is None:
            return super(QGraphicsView, self.view).mouseMoveEvent(event)
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        scene_pos = self.view.mapToScene(event.pos())
        x, y, _ = self._snap_to_point(scene_pos)
        start_ent = self.sketch.get_entity(self._start_point)
        if not start_ent:
            return
        sx, sy = float(start_ent["x"]), float(start_ent["y"])

        self._clear_preview()
        if self.mode == "line":
            self._preview_item = self.scene.addLine(sx, -sy, x, -y)
            self._preview_item.setPen(QPen(QColor(100, 150, 255), 0.1, Qt.PenStyle.DashLine))
        elif self.mode == "circle":
            rad = ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5
            self._preview_item = self.scene.addEllipse(sx - rad, -sy - rad, 2 * rad, 2 * rad)
            self._preview_item.setPen(QPen(QColor(100, 150, 255), 0.1, Qt.PenStyle.DashLine))
            self._preview_item.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def _on_mouse_release(self, event) -> None:
        if self.sketch is None or self._start_point is None or event.button() != Qt.MouseButton.LeftButton:
            return super(QGraphicsView, self.view).mouseReleaseEvent(event)
        scene_pos = self.view.mapToScene(event.pos())
        x, y, snapped_id = self._snap_to_point(scene_pos)
        start_ent = self.sketch.get_entity(self._start_point)
        if not start_ent:
            self._start_point = None
            self._clear_preview()
            return

        if self.mode == "line":
            end_id = snapped_id or self.sketch.add_point(x, y)
            if end_id != self._start_point:
                self.sketch.add_line(self._start_point, end_id)
        elif self.mode == "circle":
            rad = ((x - float(start_ent["x"])) ** 2 + (y - float(start_ent["y"])) ** 2) ** 0.5
            if rad > 0.01:
                self.sketch.add_circle(self._start_point, rad)

        self._start_point = None
        self._clear_preview()
        self.refresh()
        self.sketch_changed.emit()
