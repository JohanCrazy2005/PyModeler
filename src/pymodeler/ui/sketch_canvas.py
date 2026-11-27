"""Visual 2D sketch canvas using QGraphicsView / QGraphicsScene.

Supports drawing modes (point, line, circle, rectangle, arc, arc3), snapping,
live preview, selection highlight, multi-select (Shift), and box select.
Entity IDs are stored in QGraphicsItem.data(0) for tests and selection.
"""

from __future__ import annotations

import math
from typing import Optional, Set, List, Tuple

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QPoint
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QPolygonF
from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QWidget,
)

from pymodeler.core import Sketch


SNAP_DISTANCE = 8.0  # pixels (converted roughly via view transform; scene units used here as mm)
POINT_RADIUS = 3.0
SELECT_TOL = 6.0


def _circle_from_3_points(
    x1: float, y1: float, x2: float, y2: float, x3: float, y3: float
) -> Optional[Tuple[float, float, float]]:
    """Return (cx, cy, r) of circle through three points, or None if collinear."""
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        return None
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    return (ux, uy, r)


def _arc_angles_through(a1: float, a2: float, a3: float) -> Tuple[float, float]:
    """Return (start_angle, end_angle) in degrees for CCW arc from a1 through a2 to a3.

    Angles are normalized to [0, 360). Sweep is the shortest CCW that passes through a2.
    """
    def norm(a: float) -> float:
        return a % 360.0

    a1, a2, a3 = norm(a1), norm(a2), norm(a3)
    # Compute CCW sweep from a1 to a3 that contains a2
    def ccw_sweep(start: float, end: float) -> float:
        s = (end - start) % 360.0
        return s if s > 0 else 360.0

    sweep = ccw_sweep(a1, a3)
    # Check if a2 lies within the CCW sweep
    mid_rel = (a2 - a1) % 360.0
    if mid_rel <= sweep + 1e-6:
        return a1, a1 + sweep
    # Otherwise the other way (CW would be shorter, but we force CCW via the long way)
    return a1, a1 + (360.0 - (360.0 - sweep))


class SketchCanvasWidget(QGraphicsView):
    """Interactive 2D canvas for a Sketch."""

    sketch_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor(40, 40, 44)))

        self.sketch: Optional[Sketch] = None
        self.mode: str = "select"
        self.selected_id: Optional[str] = None
        self.selected_ids: Set[str] = set()

        # Drawing state
        self._start_point: Optional[str] = None
        self._preview_item: Optional[QGraphicsItem] = None
        self._arc_center: Optional[str] = None
        self._arc_radius: float = 0.0
        self._arc_start_angle: float = 0.0
        self._arc3_p1: Optional[str] = None
        self._arc3_p2: Optional[str] = None
        self._box_start: Optional[QPointF] = None
        self._box_item: Optional[QGraphicsItem] = None
        self._drag_entity: Optional[str] = None
        self._snap_tol = 0.5  # scene units

    def set_sketch(self, sketch: Optional[Sketch]) -> None:
        self.sketch = sketch
        self.selected_id = None
        self.selected_ids.clear()
        self.refresh()

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self._clear_preview()
        self._clear_box()
        if mode != "select":
            self.selected_ids.clear()
            self.selected_id = None

    def refresh(self) -> None:
        """Rebuild scene items from current sketch entities."""
        self.scene.clear()
        self._preview_item = None
        self._box_item = None
        if self.sketch is None:
            return

        # Draw in order: lines/arcs/circles then points on top
        for ent in self.sketch.entities:
            self._draw_entity(ent)

        # Draw constraint and dimension badges
        self._draw_badges()

        # Highlight selected
        for item in self.scene.items():
            eid = item.data(0)
            if eid and (eid == self.selected_id or eid in self.selected_ids):
                if isinstance(item, QGraphicsEllipseItem) and item.rect().width() < 10:
                    item.setBrush(QBrush(QColor(255, 200, 50)))
                    item.setPen(QPen(QColor(255, 220, 80), 2))
                else:
                    pen = item.pen()
                    pen.setColor(QColor(255, 200, 50))
                    pen.setWidth(2)
                    item.setPen(pen)

    def _draw_badges(self) -> None:
        """Draw simple constraint and dimension badges near related entities."""
        if self.sketch is None:
            return

        # Constraint type to short label
        ctype_labels = {
            "horizontal": "H",
            "vertical": "V",
            "coincident": "C",
            "parallel": "//",
            "perpendicular": "⊥",
            "equal": "=",
            "tangent": "T",
            "fixed": "F",
            "concentric": "◎",
            "midpoint": "M",
        }

        for con in self.sketch.constraints:
            label = ctype_labels.get(con.get("type", ""), "?")
            ents = con.get("entities") or []
            if not ents:
                continue
            pos = self._badge_position_for_entity(ents[0])
            if pos is None:
                continue
            self._add_badge(pos[0], pos[1], label, tooltip=f"{con.get('type')} {ents}")

        for dim in self.sketch.dimensions:
            dtype = dim.get("type", "dim")
            value = dim.get("value", "")
            label = f"{dtype[:1].upper()}:{value}"
            ents = dim.get("entities") or []
            if not ents:
                continue
            pos = self._badge_position_for_entity(ents[0])
            if pos is None:
                continue
            # Offset dimensions a bit further
            ox, oy = pos
            self._add_badge(ox + 4.0, oy + 4.0, label, tooltip=f"{dtype}={value} {ents}", is_dim=True)

    def _badge_position_for_entity(self, eid: str) -> Optional[Tuple[float, float]]:
        """Return a good (x, y) for a badge near an entity."""
        ent = self.sketch.get_entity(eid) if self.sketch else None
        if not ent:
            return None
        etype = ent.get("type")
        if etype == "point":
            return (ent["x"], ent["y"])
        if etype == "line":
            s = self.sketch.get_entity(ent["start_point"])
            e = self.sketch.get_entity(ent["end_point"])
            if s and e:
                return ((s["x"] + e["x"]) / 2.0, (s["y"] + e["y"]) / 2.0)
        if etype in ("circle", "arc"):
            c = self.sketch.get_entity(ent["center"])
            if c:
                return (c["x"], c["y"])
        return None

    def _add_badge(self, x: float, y: float, text: str, tooltip: str = "", is_dim: bool = False) -> None:
        """Add a small text badge at (x, y)."""
        item = QGraphicsTextItem(text)
        item.setPos(x, y - 6)
        item.setDefaultTextColor(QColor(255, 220, 100) if is_dim else QColor(140, 220, 140))
        item.setZValue(20)
        item.setToolTip(tooltip)
        # Store a marker so tests can find badges
        item.setData(1, "badge")
        self.scene.addItem(item)

    def _draw_entity(self, ent: dict) -> None:
        eid = ent["id"]
        etype = ent["type"]
        pen = QPen(QColor(180, 200, 220), 1.5)
        brush = QBrush(QColor(100, 140, 180))

        if etype == "point":
            x, y = ent["x"], ent["y"]
            item = self.scene.addEllipse(x - POINT_RADIUS, y - POINT_RADIUS,
                                          POINT_RADIUS * 2, POINT_RADIUS * 2, pen, brush)
            item.setData(0, eid)
            item.setZValue(10)
        elif etype == "line":
            start = self.sketch.get_entity(ent["start_point"])
            end = self.sketch.get_entity(ent["end_point"])
            if start and end:
                item = self.scene.addLine(start["x"], start["y"], end["x"], end["y"], pen)
                item.setData(0, eid)
        elif etype == "circle":
            center = self.sketch.get_entity(ent["center"])
            if center:
                r = ent["radius"]
                item = self.scene.addEllipse(center["x"] - r, center["y"] - r, r * 2, r * 2, pen)
                item.setData(0, eid)
        elif etype == "arc":
            center = self.sketch.get_entity(ent["center"])
            if center:
                r = ent["radius"]
                sa = ent["start_angle"]
                ea = ent["end_angle"]
                # Approximate arc with path
                path = self._arc_path(center["x"], center["y"], r, sa, ea)
                item = self.scene.addPath(path, pen)
                item.setData(0, eid)

    def _arc_path(self, cx: float, cy: float, r: float, sa_deg: float, ea_deg: float):
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        steps = max(8, int(abs(ea_deg - sa_deg) / 5))
        for i in range(steps + 1):
            t = i / steps
            ang = math.radians(sa_deg + t * ((ea_deg - sa_deg) % 360))
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        return path

    def _clear_preview(self) -> None:
        if self._preview_item:
            self.scene.removeItem(self._preview_item)
            self._preview_item = None

    def _clear_box(self) -> None:
        if self._box_item:
            self.scene.removeItem(self._box_item)
            self._box_item = None
        self._box_start = None

    def _find_or_add_point(self, pos: QPointF, tol: float = 0.25) -> str:
        """Snap to existing point or add a new one. Returns entity id."""
        if self.sketch is None:
            return ""
        best = None
        best_d = tol
        for ent in self.sketch.entities:
            if ent["type"] == "point":
                d = math.hypot(ent["x"] - pos.x(), ent["y"] - pos.y())
                if d < best_d:
                    best_d = d
                    best = ent["id"]
        if best:
            return best
        return self.sketch.add_point(pos.x(), pos.y())

    def mousePressEvent(self, event):
        if self.sketch is None or event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        pos = self.mapToScene(event.position().toPoint())
        modifiers = event.modifiers()

        if self.mode == "select":
            # Box select start or click select
            hit = self._hit_test(pos)
            if hit:
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    if hit in self.selected_ids:
                        self.selected_ids.remove(hit)
                    else:
                        self.selected_ids.add(hit)
                    self.selected_id = hit
                else:
                    self.selected_ids = {hit}
                    self.selected_id = hit
                self._drag_entity = hit
            else:
                if not (modifiers & Qt.KeyboardModifier.ShiftModifier):
                    self.selected_ids.clear()
                    self.selected_id = None
                self._box_start = pos
            self.refresh()
            return

        if self.mode == "point":
            self._find_or_add_point(pos)
            self.sketch.validate()
            self.refresh()
            self.sketch_changed.emit()
            return

        if self.mode in ("line", "rectangle", "circle"):
            self._start_point = self._find_or_add_point(pos)
            return

        if self.mode == "arc":
            if self._arc_center is None:
                self._arc_center = self._find_or_add_point(pos)
            elif self._arc_radius == 0.0:
                c = self.sketch.get_entity(self._arc_center)
                if c:
                    self._arc_radius = math.hypot(pos.x() - c["x"], pos.y() - c["y"])
                    self._arc_start_angle = math.degrees(math.atan2(pos.y() - c["y"], pos.x() - c["x"]))
            else:
                # third click: end angle
                c = self.sketch.get_entity(self._arc_center)
                if c:
                    ea = math.degrees(math.atan2(pos.y() - c["y"], pos.x() - c["x"]))
                    self.sketch.add_arc(self._arc_center, self._arc_radius, self._arc_start_angle, ea)
                    self.sketch.validate()
                    self._arc_center = None
                    self._arc_radius = 0.0
                    self.refresh()
                    self.sketch_changed.emit()
            return

        if self.mode == "arc3":
            pid = self._find_or_add_point(pos)
            if self._arc3_p1 is None:
                self._arc3_p1 = pid
            elif self._arc3_p2 is None:
                self._arc3_p2 = pid
            else:
                p1 = self.sketch.get_entity(self._arc3_p1)
                p2 = self.sketch.get_entity(self._arc3_p2)
                p3 = self.sketch.get_entity(pid)
                if p1 and p2 and p3:
                    circ = _circle_from_3_points(p1["x"], p1["y"], p2["x"], p2["y"], p3["x"], p3["y"])
                    if circ:
                        cx, cy, r = circ
                        center_id = self._find_or_add_point(QPointF(cx, cy), tol=0.25)
                        a1 = math.degrees(math.atan2(p1["y"] - cy, p1["x"] - cx))
                        a2 = math.degrees(math.atan2(p2["y"] - cy, p2["x"] - cx))
                        a3 = math.degrees(math.atan2(p3["y"] - cy, p3["x"] - cx))
                        sa, ea = _arc_angles_through(a1, a2, a3)
                        self.sketch.add_arc(center_id, r, sa, ea)
                        self.sketch.validate()
                        self.refresh()
                        self.sketch_changed.emit()
                self._arc3_p1 = None
                self._arc3_p2 = None
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.sketch is None:
            return super().mouseMoveEvent(event)
        pos = self.mapToScene(event.position().toPoint())

        if self.mode == "select" and self._box_start is not None:
            self._update_box(self._box_start, pos)
            return

        if self.mode == "select" and self._drag_entity and event.buttons() & Qt.MouseButton.LeftButton:
            # Simple drag for points
            ent = self.sketch.get_entity(self._drag_entity)
            if ent and ent["type"] == "point":
                self.sketch.update_point(self._drag_entity, pos.x(), pos.y())
                self.refresh()
            return

        # Live preview for drawing modes
        self._clear_preview()
        pen = QPen(QColor(120, 180, 255), 1, Qt.PenStyle.DashLine)
        if self.mode == "line" and self._start_point:
            start = self.sketch.get_entity(self._start_point)
            if start:
                self._preview_item = self.scene.addLine(start["x"], start["y"], pos.x(), pos.y(), pen)
        elif self.mode == "circle" and self._start_point:
            start = self.sketch.get_entity(self._start_point)
            if start:
                r = math.hypot(pos.x() - start["x"], pos.y() - start["y"])
                self._preview_item = self.scene.addEllipse(start["x"] - r, start["y"] - r, r * 2, r * 2, pen)
        elif self.mode == "rectangle" and self._start_point:
            start = self.sketch.get_entity(self._start_point)
            if start:
                rect = QRectF(start["x"], start["y"], pos.x() - start["x"], pos.y() - start["y"]).normalized()
                self._preview_item = self.scene.addRect(rect, pen)
        elif self.mode == "arc" and self._arc_center and self._arc_radius > 0:
            c = self.sketch.get_entity(self._arc_center)
            if c:
                ea = math.degrees(math.atan2(pos.y() - c["y"], pos.x() - c["x"]))
                path = self._arc_path(c["x"], c["y"], self._arc_radius, self._arc_start_angle, ea)
                self._preview_item = self.scene.addPath(path, pen)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.sketch is None or event.button() != Qt.MouseButton.LeftButton:
            return super().mouseReleaseEvent(event)
        pos = self.mapToScene(event.position().toPoint())

        if self.mode == "select" and self._box_start is not None:
            self._finish_box_select(self._box_start, pos)
            self._clear_box()
            self.refresh()
            return

        self._drag_entity = None
        self._clear_preview()

        if self.mode == "line" and self._start_point:
            end = self._find_or_add_point(pos)
            if end != self._start_point:
                self.sketch.add_line(self._start_point, end)
                self.sketch.validate()
                self.refresh()
                self.sketch_changed.emit()
            self._start_point = None
            return

        if self.mode == "circle" and self._start_point:
            start = self.sketch.get_entity(self._start_point)
            if start:
                r = math.hypot(pos.x() - start["x"], pos.y() - start["y"])
                if r > 0.1:
                    self.sketch.add_circle(self._start_point, r)
                    self.sketch.validate()
                    self.refresh()
                    self.sketch_changed.emit()
            self._start_point = None
            return

        if self.mode == "rectangle" and self._start_point:
            start = self.sketch.get_entity(self._start_point)
            if start:
                x1, y1 = start["x"], start["y"]
                x2, y2 = pos.x(), pos.y()
                if abs(x2 - x1) > 0.1 and abs(y2 - y1) > 0.1:
                    p_br = self.sketch.add_point(x2, y1)
                    p_tr = self.sketch.add_point(x2, y2)
                    p_tl = self.sketch.add_point(x1, y2)
                    self.sketch.add_line(self._start_point, p_br)
                    self.sketch.add_line(p_br, p_tr)
                    self.sketch.add_line(p_tr, p_tl)
                    self.sketch.add_line(p_tl, self._start_point)
                    self.sketch.validate()
                    self.refresh()
                    self.sketch_changed.emit()
            self._start_point = None
            return

        super().mouseReleaseEvent(event)

    def _hit_test(self, pos: QPointF) -> Optional[str]:
        """Return closest entity id within tolerance, or None."""
        if self.sketch is None:
            return None
        best = None
        best_d = SELECT_TOL
        for ent in self.sketch.entities:
            d = self._distance_to_entity(pos, ent)
            if d is not None and d < best_d:
                best_d = d
                best = ent["id"]
        return best

    def _distance_to_entity(self, pos: QPointF, ent: dict) -> Optional[float]:
        etype = ent["type"]
        if etype == "point":
            return math.hypot(ent["x"] - pos.x(), ent["y"] - pos.y())
        if etype == "line":
            s = self.sketch.get_entity(ent["start_point"])
            e = self.sketch.get_entity(ent["end_point"])
            if s and e:
                return self._point_to_segment(pos, s["x"], s["y"], e["x"], e["y"])
        if etype == "circle":
            c = self.sketch.get_entity(ent["center"])
            if c:
                d = abs(math.hypot(pos.x() - c["x"], pos.y() - c["y"]) - ent["radius"])
                return d
        if etype == "arc":
            c = self.sketch.get_entity(ent["center"])
            if c:
                d = abs(math.hypot(pos.x() - c["x"], pos.y() - c["y"]) - ent["radius"])
                # crude: also check angle range later if needed
                return d
        return None

    @staticmethod
    def _point_to_segment(p: QPointF, x1: float, y1: float, x2: float, y2: float) -> float:
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(p.x() - x1, p.y() - y1)
        t = max(0.0, min(1.0, ((p.x() - x1) * dx + (p.y() - y1) * dy) / (dx * dx + dy * dy)))
        px, py = x1 + t * dx, y1 + t * dy
        return math.hypot(p.x() - px, p.y() - py)

    def _update_box(self, start: QPointF, end: QPointF) -> None:
        self._clear_box()
        rect = QRectF(start, end).normalized()
        pen = QPen(QColor(100, 160, 255), 1, Qt.PenStyle.DashLine)
        brush = QBrush(QColor(100, 160, 255, 40))
        self._box_item = self.scene.addRect(rect, pen, brush)
        self._box_start = start

    def _finish_box_select(self, start: QPointF, end: QPointF) -> None:
        rect = QRectF(start, end).normalized()
        if rect.width() < 1 and rect.height() < 1:
            return
        new_sel = set()
        for ent in self.sketch.entities:
            if self._entity_in_rect(ent, rect):
                new_sel.add(ent["id"])
        self.selected_ids = new_sel
        self.selected_id = next(iter(new_sel), None)

    def _entity_in_rect(self, ent: dict, rect: QRectF) -> bool:
        etype = ent["type"]
        if etype == "point":
            return rect.contains(QPointF(ent["x"], ent["y"]))
        if etype == "line":
            s = self.sketch.get_entity(ent["start_point"])
            e = self.sketch.get_entity(ent["end_point"])
            if s and e:
                return (rect.contains(QPointF(s["x"], s["y"])) or
                        rect.contains(QPointF(e["x"], e["y"])) or
                        self._segment_intersects_rect(s["x"], s["y"], e["x"], e["y"], rect))
        if etype in ("circle", "arc"):
            c = self.sketch.get_entity(ent["center"])
            if c:
                # bounding box approximation
                r = ent["radius"]
                bb = QRectF(c["x"] - r, c["y"] - r, r * 2, r * 2)
                return rect.intersects(bb)
        return False

    @staticmethod
    def _segment_intersects_rect(x1, y1, x2, y2, rect: QRectF) -> bool:
        # Simple: check if either endpoint or midpoint is inside, or edges cross (approximate)
        mid = QPointF((x1 + x2) / 2, (y1 + y2) / 2)
        return rect.contains(mid)
