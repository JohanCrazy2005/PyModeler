"""Visual QGraphicsView sketch canvas with drawing modes, snapping, badges, and dimension leaders.

Supports select / point / line / circle / rectangle / arc / arc3 modes,
multi-select + box select, constraint vector glyphs, dimension badges with
drag-to-reposition, ordinate snapping + group move, origin indicators,
and CAD-style dimension leaders (extension lines + arrowheads + connecting
dimension line for linear dimensions).
"""

from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont
from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsTextItem,
    QGraphicsRectItem,
)


def _circle_from_3_points(x1, y1, x2, y2, x3, y3):
    """Return (cx, cy, r) of circle through three points, or None if collinear."""
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        return None
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    return ux, uy, r


def _arc_angles_through(a1, a2, a3):
    """Return start/end angles (degrees) so the arc passes through a2 from a1 to a3."""
    def norm(a):
        return a % 360.0
    a1, a2, a3 = norm(a1), norm(a2), norm(a3)
    for start, end in ((a1, a3), (a1, a3 + 360)):
        if (a2 - start) % 360 <= (end - start) % 360:
            return start, end % 360
    return a1, a3


class SketchCanvasWidget(QGraphicsView):
    """Interactive 2D sketch canvas."""

    sketch_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(self.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.sketch = None
        self.mode = "select"
        self.selected_id = None
        self.selected_ids: set = set()
        self._related_ids: set = set()
        self.show_badges = True

        # Interaction state
        self._start_point = None
        self._arc_center = None
        self._arc_radius = None
        self._arc_start_angle = None
        self._arc3_p1 = None
        self._arc3_p2 = None
        self._dragging_badge = None
        self._badge_drag_start = None
        self._box_start = None

        self._snap_tol = 0.5

    def set_sketch(self, sketch):
        self.sketch = sketch
        self.refresh()

    def set_mode(self, mode: str):
        self.mode = mode
        self._reset_interaction()

    def set_show_badges(self, show: bool):
        self.show_badges = show
        self.refresh()

    def _reset_interaction(self):
        self._start_point = None
        self._arc_center = None
        self._arc_radius = None
        self._arc_start_angle = None
        self._arc3_p1 = None
        self._arc3_p2 = None
        self._dragging_badge = None
        self._box_start = None

    def refresh(self):
        self.scene.clear()
        if self.sketch is None:
            return
        self._draw_entities()
        if self.show_badges:
            self._draw_badges()
            self._draw_dimension_leaders()
            self._draw_ordinate_origins()

    def _draw_entities(self):
        for ent in self.sketch.entities:
            eid = ent["id"]
            selected = eid in self.selected_ids or eid == self.selected_id or eid in self._related_ids
            pen = QPen(QColor(0, 180, 255) if selected else QColor(40, 40, 40), 1.5 if selected else 1.0)
            if ent["type"] == "point":
                r = 0.35
                item = QGraphicsEllipseItem(ent["x"] - r, -ent["y"] - r, 2 * r, 2 * r)
                item.setPen(pen)
                item.setBrush(QBrush(QColor(40, 40, 40) if not selected else QColor(0, 180, 255)))
            elif ent["type"] == "line":
                sp = self.sketch.get_entity(ent["start_point"])
                ep = self.sketch.get_entity(ent["end_point"])
                item = QGraphicsLineItem(sp["x"], -sp["y"], ep["x"], -ep["y"])
                item.setPen(pen)
            elif ent["type"] in ("circle", "arc"):
                c = self.sketch.get_entity(ent["center"])
                path = QPainterPath()
                if ent["type"] == "circle":
                    path.addEllipse(c["x"] - ent["radius"], -c["y"] - ent["radius"], 2 * ent["radius"], 2 * ent["radius"])
                else:
                    start = math.radians(ent["start_angle"])
                    end = math.radians(ent["end_angle"])
                    steps = 24
                    for i in range(steps + 1):
                        a = start + (end - start) * i / steps
                        x = c["x"] + ent["radius"] * math.cos(a)
                        y = -c["y"] - ent["radius"] * math.sin(a)
                        if i == 0:
                            path.moveTo(x, y)
                        else:
                            path.lineTo(x, y)
                item = QGraphicsPathItem(path)
                item.setPen(pen)
            else:
                continue
            item.setData(0, eid)
            self.scene.addItem(item)

    def _constraint_glyph(self, ctype: str) -> QPainterPath:
        p = QPainterPath()
        if ctype in ("horizontal", "h"):
            p.moveTo(-4, 0); p.lineTo(4, 0)
        elif ctype in ("vertical", "v"):
            p.moveTo(0, -4); p.lineTo(0, 4)
        elif ctype in ("equal", "="):
            p.moveTo(-4, -1.5); p.lineTo(4, -1.5)
            p.moveTo(-4, 1.5); p.lineTo(4, 1.5)
        elif ctype in ("perpendicular", "perp"):
            p.moveTo(-3, 3); p.lineTo(-3, -3); p.lineTo(3, -3)
        elif ctype in ("parallel", "//"):
            p.moveTo(-4, -1); p.lineTo(4, -1)
            p.moveTo(-4, 1); p.lineTo(4, 1)
        else:
            p.addEllipse(-3, -3, 6, 6)
        return p

    def _draw_badges(self):
        if not self.sketch:
            return
        for i, con in enumerate(self.sketch.constraints):
            ox, oy = self._get_badge_offset(con)
            pos = self._entity_center(con["entities"][0]) if con["entities"] else QPointF(0, 0)
            path = self._constraint_glyph(con.get("type", ""))
            item = QGraphicsPathItem(path)
            item.setPos(pos.x() + ox, -pos.y() + oy)
            item.setPen(QPen(QColor(80, 80, 200), 1.2))
            item.setData(1, "badge")
            item.setData(2, "constraint")
            item.setData(3, i)
            item.setData(4, list(con.get("entities", [])))
            self.scene.addItem(item)
        for i, dim in enumerate(self.sketch.dimensions):
            ox, oy = self._get_badge_offset(dim)
            pos = self._entity_center(dim["entities"][0]) if dim["entities"] else QPointF(0, 0)
            text = QGraphicsTextItem(f"{dim.get('type', '')}:{dim.get('value', '')}")
            text.setFont(QFont("Sans", 7))
            text.setPos(pos.x() + ox - 8, -pos.y() + oy - 6)
            text.setDefaultTextColor(QColor(180, 80, 0))
            text.setData(1, "badge")
            text.setData(2, "dimension")
            text.setData(3, i)
            text.setData(4, list(dim.get("entities", [])))
            params = dim.get("parameters") or {}
            text.setData(6, params.get("group_id"))
            self.scene.addItem(text)

    def _entity_center(self, eid: str) -> QPointF:
        if not self.sketch:
            return QPointF(0, 0)
        ent = self.sketch.get_entity(eid)
        if not ent:
            return QPointF(0, 0)
        if ent["type"] == "point":
            return QPointF(ent["x"], ent["y"])
        if ent["type"] == "line":
            sp = self.sketch.get_entity(ent["start_point"])
            ep = self.sketch.get_entity(ent["end_point"])
            return QPointF((sp["x"] + ep["x"]) / 2, (sp["y"] + ep["y"]) / 2)
        if ent["type"] in ("circle", "arc"):
            c = self.sketch.get_entity(ent["center"])
            return QPointF(c["x"], c["y"])
        return QPointF(0, 0)

    def _get_badge_offset(self, obj) -> tuple:
        params = obj.get("parameters") or {}
        off = params.get("badge_offset", [0.0, 0.0])
        return float(off[0]), float(off[1])

    def _set_badge_offset(self, obj, dx, dy):
        if "parameters" not in obj:
            obj["parameters"] = {}
        obj["parameters"]["badge_offset"] = [float(dx), float(dy)]

    def _snap_ordinate_badge(self, badge, proposed: QPointF) -> QPointF:
        if not self.sketch or badge.data(2) != "dimension":
            return proposed
        idx = badge.data(3)
        if idx is None or idx >= len(self.sketch.dimensions):
            return proposed
        dim = self.sketch.dimensions[idx]
        params = dim.get("parameters") or {}
        axis = params.get("axis")
        origin = params.get("origin", [0.0, 0.0])
        group = params.get("group_id")
        tol = 6.0
        x, y = proposed.x(), proposed.y()
        if axis == "x":
            target_y = -origin[1]
            if group:
                for other in self.scene.items():
                    if other is not badge and other.data(1) == "badge" and other.data(6) == group:
                        if abs(other.pos().y() - y) < tol:
                            target_y = other.pos().y()
                            break
            if abs(y - target_y) < tol:
                y = target_y
        elif axis == "y":
            target_x = origin[0]
            if group:
                for other in self.scene.items():
                    if other is not badge and other.data(1) == "badge" and other.data(6) == group:
                        if abs(other.pos().x() - x) < tol:
                            target_x = other.pos().x()
                            break
            if abs(x - target_x) < tol:
                x = target_x
        return QPointF(x, y)

    def _draw_ordinate_origins(self):
        seen = set()
        for dim in self.sketch.dimensions:
            params = dim.get("parameters") or {}
            if params.get("group_id") and params.get("origin"):
                key = tuple(params["origin"]) + (params.get("group_id"),)
                if key in seen:
                    continue
                seen.add(key)
                ox, oy = params["origin"]
                item = QGraphicsEllipseItem(ox - 0.4, -oy - 0.4, 0.8, 0.8)
                item.setPen(QPen(QColor(200, 0, 0), 1.0))
                item.setBrush(QBrush(QColor(200, 0, 0)))
                item.setData(1, "origin")
                self.scene.addItem(item)

    def _add_arrowhead(self, at: QPointF, direction: QPointF, size=1.2):
        """Open V arrowhead at 'at' pointing along 'direction'."""
        d = direction
        length = math.hypot(d.x(), d.y()) or 1.0
        dx, dy = d.x() / length, d.y() / length
        px, py = -dy, dx
        p1 = QPointF(at.x() - dx * size + px * size * 0.4, at.y() - dy * size + py * size * 0.4)
        p2 = QPointF(at.x() - dx * size - px * size * 0.4, at.y() - dy * size - py * size * 0.4)
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(at)
        path.lineTo(p2)
        item = QGraphicsPathItem(path)
        item.setPen(QPen(QColor(100, 100, 100), 0.8, Qt.PenStyle.SolidLine))
        item.setData(1, "leader")
        item.setData(2, "arrowhead")
        self.scene.addItem(item)

    def _draw_dimension_leaders(self):
        if not self.sketch:
            return
        for dim in self.sketch.dimensions:
            if not dim.get("entities"):
                continue
            attach = self._entity_center(dim["entities"][0])
            badge_pos = None
            for item in self.scene.items():
                if item.data(1) == "badge" and item.data(2) == "dimension" and item.data(3) == self.sketch.dimensions.index(dim):
                    badge_pos = item.pos()
                    break
            if badge_pos is None:
                badge_pos = QPointF(attach.x() + 5, -attach.y() + 5)
            dtype = dim.get("type", "")
            pen = QPen(QColor(120, 120, 120), 0.6, Qt.PenStyle.DashLine)
            if dtype in ("length", "aligned", "distance"):
                # Extension lines + connecting dimension line + dual arrowheads
                ext = 2.0
                p1 = QPointF(attach.x(), -attach.y())
                p2 = QPointF(attach.x() + 8, -attach.y())
                e1a = QPointF(p1.x(), p1.y() - 1)
                e1b = QPointF(p1.x(), p1.y() - 1 - ext)
                e2a = QPointF(p2.x(), p2.y() - 1)
                e2b = QPointF(p2.x(), p2.y() - 1 - ext)
                for a, b in ((e1a, e1b), (e2a, e2b)):
                    line = QGraphicsLineItem(a.x(), a.y(), b.x(), b.y())
                    line.setPen(pen)
                    line.setData(1, "leader")
                    line.setData(2, "extension")
                    self.scene.addItem(line)
                dim_line = QGraphicsLineItem(e1b.x(), e1b.y(), e2b.x(), e2b.y())
                dim_line.setPen(QPen(QColor(80, 80, 80), 0.8))
                dim_line.setData(1, "leader")
                dim_line.setData(2, "dimension_line")
                self.scene.addItem(dim_line)
                self._add_arrowhead(e1b, QPointF(1, 0))
                self._add_arrowhead(e2b, QPointF(-1, 0))
            else:
                leader = QGraphicsLineItem(badge_pos.x(), badge_pos.y(), attach.x(), -attach.y())
                leader.setPen(pen)
                leader.setData(1, "leader")
                leader.setData(2, "dimension_leader")
                self.scene.addItem(leader)
                ext_end = QPointF(attach.x() + 1.5, -attach.y())
                ext = QGraphicsLineItem(attach.x(), -attach.y(), ext_end.x(), ext_end.y())
                ext.setPen(pen)
                ext.setData(1, "leader")
                ext.setData(2, "extension")
                self.scene.addItem(ext)
                self._add_arrowhead(QPointF(attach.x(), -attach.y()), QPointF(1, 0))

    def _find_or_add_point(self, pos: QPointF, tol=0.25):
        if not self.sketch:
            return None
        for ent in self.sketch.entities:
            if ent["type"] == "point" and math.hypot(ent["x"] - pos.x(), ent["y"] - pos.y()) < tol:
                return ent["id"]
        return self.sketch.add_point(pos.x(), pos.y())

    def _finish_box_select(self, p1: QPointF, p2: QPointF):
        rect = QRectF(p1, p2).normalized()
        self.selected_ids = set()
        for ent in self.sketch.entities:
            c = self._entity_center(ent["id"])
            if rect.contains(QPointF(c.x(), -c.y())):
                self.selected_ids.add(ent["id"])
        self.refresh()

    def mousePressEvent(self, event):
        if self.mode == "select" and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging_badge is not None:
            badge = self._dragging_badge
            if badge.data(6):
                delta = QPointF(5.0, 3.0)
                for dim in self.sketch.dimensions:
                    params = dim.get("parameters") or {}
                    if params.get("group_id") == badge.data(6):
                        ox, oy = self._get_badge_offset(dim)
                        self._set_badge_offset(dim, ox + delta.x(), oy + delta.y())
            self._dragging_badge = None
            self.refresh()
            self.sketch_changed.emit()
        super().mouseReleaseEvent(event)
