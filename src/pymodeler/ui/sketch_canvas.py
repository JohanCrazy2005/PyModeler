"""Visual 2D sketch canvas using QGraphicsView / QGraphicsScene.

Supports drawing modes (point, line, circle, rectangle, arc, arc3), snapping,
live preview, selection highlight, multi-select (Shift), and box select.
Entity IDs are stored in QGraphicsItem.data(0) for tests and selection.
"""

from __future__ import annotations

import math
from typing import Optional, Set, List, Tuple

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QPoint
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QPolygonF, QPainterPath
from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QWidget,
    QInputDialog,
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



def _constraint_glyph_path(ctype: str) -> QPainterPath:
    """Vector glyph path for a constraint type, centered at origin (~8 units)."""
    path = QPainterPath()
    s = 4.0
    if ctype == "horizontal":
        path.moveTo(-s, 0)
        path.lineTo(s, 0)
    elif ctype == "vertical":
        path.moveTo(0, -s)
        path.lineTo(0, s)
    elif ctype == "coincident":
        path.addEllipse(-1.6, -1.6, 3.2, 3.2)
        path.addEllipse(-0.7, -0.7, 1.4, 1.4)
    elif ctype == "parallel":
        path.moveTo(-s, -1.6)
        path.lineTo(s, -1.6)
        path.moveTo(-s, 1.6)
        path.lineTo(s, 1.6)
    elif ctype == "perpendicular":
        path.moveTo(-s, 0)
        path.lineTo(0, 0)
        path.lineTo(0, s)
    elif ctype == "equal":
        path.moveTo(-s, -1.2)
        path.lineTo(s, -1.2)
        path.moveTo(-s, 1.2)
        path.lineTo(s, 1.2)
    elif ctype == "tangent":
        path.addEllipse(-s * 0.7, -s * 0.7, s * 1.4, s * 1.4)
        path.moveTo(s * 0.7, -s)
        path.lineTo(s * 0.7, s)
    elif ctype == "fixed":
        path.moveTo(-1.2, -s)
        path.lineTo(-1.2, s)
        path.moveTo(-1.2, 0)
        path.lineTo(s * 0.5, 0)
        path.moveTo(-1.2, s * 0.5)
        path.lineTo(s * 0.3, s * 0.5)
    elif ctype == "concentric":
        path.addEllipse(-s, -s, s * 2, s * 2)
        path.addEllipse(-s * 0.45, -s * 0.45, s * 0.9, s * 0.9)
    elif ctype == "midpoint":
        path.moveTo(0, -s)
        path.lineTo(-s * 0.7, s * 0.6)
        path.lineTo(s * 0.7, s * 0.6)
        path.closeSubpath()
    else:
        path.addEllipse(-1.2, -1.2, 2.4, 2.4)
    return path


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
        self.show_badges: bool = True
        self._hovered_badge: Optional[QGraphicsItem] = None
        self._related_ids: Set[str] = set()
        self._dragging_badge: Optional[QGraphicsItem] = None
        self._badge_drag_start: Optional[QPointF] = None
        self._badge_orig_pos: Optional[QPointF] = None
        self._dragging_group_badges: List[QGraphicsItem] = []

    def set_show_badges(self, show: bool) -> None:
        """Toggle visibility of constraint and dimension badges."""
        self.show_badges = show
        self.refresh()

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

        # Highlight selected and related (from badge hover/click)
        related = getattr(self, "_related_ids", set())
        for item in self.scene.items():
            eid = item.data(0)
            if eid and (eid == self.selected_id or eid in self.selected_ids or eid in related):
                if isinstance(item, QGraphicsEllipseItem) and item.rect().width() < 10:
                    item.setBrush(QBrush(QColor(255, 200, 50)))
                    item.setPen(QPen(QColor(255, 220, 80), 2))
                else:
                    pen = item.pen()
                    color = QColor(120, 220, 255) if eid in related and eid not in self.selected_ids else QColor(255, 200, 50)
                    pen.setColor(color)
                    pen.setWidth(2)
                    item.setPen(pen)

    def _draw_badges(self) -> None:
        """Draw simple constraint and dimension badges near related entities."""
        if self.sketch is None or not self.show_badges:
            return

        # Constraint type to short label (glyphs)
        ctype_labels = {
            "horizontal": "H",
            "vertical": "V",
            "coincident": "C",
            "parallel": "//",
            "perpendicular": "â¥",
            "equal": "=",
            "tangent": "T",
            "fixed": "F",
            "concentric": "â",
            "midpoint": "M",
        }

        for idx, con in enumerate(self.sketch.constraints):
            label = ctype_labels.get(con.get("type", ""), "?")
            ents = con.get("entities") or []
            if not ents:
                continue
            pos = self._badge_position_for_entity(ents[0])
            if pos is None:
                continue
            ox, oy = self._get_badge_offset(con)
            self._add_badge(pos[0] + ox, pos[1] + oy, label, tooltip=f"{con.get('type')} {ents}",
                            badge_type="constraint", badge_index=idx, related_ids=ents)

        for idx, dim in enumerate(self.sketch.dimensions):
            dtype = dim.get("type", "dim")
            value = dim.get("value", "")
            label = f"{dtype[:1].upper()}:{value}"
            ents = dim.get("entities") or []
            if not ents:
                continue
            pos = self._badge_position_for_entity(ents[0])
            if pos is None:
                continue
            ox, oy = self._get_badge_offset(dim)
            # Default extra offset for dimensions so they don't overlap constraints
            self._add_badge(pos[0] + ox + 4.0, pos[1] + oy + 4.0, label, tooltip=f"{dtype}={value} {ents}",
                            is_dim=True, badge_type="dimension", badge_index=idx, related_ids=ents)

        # Draw origin indicators for ordinate dimension groups
        self._draw_ordinate_origins()

    def _draw_ordinate_origins(self) -> None:
        """Draw a small origin glyph for each unique ordinate group (or single ordinate)."""
        if self.sketch is None or not self.show_badges:
            return
        seen_groups = set()
        for dim in self.sketch.dimensions:
            if dim.get("type") != "ordinate":
                continue
            params = dim.get("parameters") or {}
            gid = params.get("group_id")
            origin = params.get("origin")
            if origin is None:
                origin = [0.0, 0.0]
            if not isinstance(origin, (list, tuple)) or len(origin) < 2:
                continue
            ox, oy = float(origin[0]), float(origin[1])
            key = gid if gid else id(dim)
            if key in seen_groups:
                continue
            seen_groups.add(key)
            # Small cross glyph at origin
            path = QPainterPath()
            s = 3.0
            path.moveTo(-s, 0)
            path.lineTo(s, 0)
            path.moveTo(0, -s)
            path.lineTo(0, s)
            # Optional circle
            path.addEllipse(-1.2, -1.2, 2.4, 2.4)
            item = QGraphicsPathItem(path)
            item.setPen(QPen(QColor(255, 160, 80), 1.6))
            item.setBrush(QBrush(QColor(255, 160, 80, 30)))
            item.setPos(ox, oy)
            item.setZValue(25)
            item.setToolTip(f"Ordinate origin {gid or ''}")
            item.setData(1, "origin")
            item.setData(6, gid)
            self.scene.addItem(item)

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

    def _get_badge_offset(self, obj: dict) -> Tuple[float, float]:
        """Return (dx, dy) display offset stored in parameters.badge_offset."""
        params = obj.get("parameters") or {}
        off = params.get("badge_offset")
        if isinstance(off, (list, tuple)) and len(off) >= 2:
            try:
                return float(off[0]), float(off[1])
            except (TypeError, ValueError):
                pass
        return 0.0, 0.0

    def _set_badge_offset(self, obj: dict, dx: float, dy: float) -> None:
        """Store display offset in parameters.badge_offset (schema-safe)."""
        if "parameters" not in obj or not isinstance(obj["parameters"], dict):
            obj["parameters"] = {}
        obj["parameters"]["badge_offset"] = [float(dx), float(dy)]

    def _add_badge(self, x: float, y: float, text: str, tooltip: str = "", is_dim: bool = False,
                   badge_type: str = "constraint", badge_index: int = -1,
                   related_ids: Optional[List[str]] = None) -> None:
        """Add a badge at (x, y). Constraints use vector path glyphs; dimensions use text."""
        if not is_dim and badge_type == "constraint":
            # True vector glyph
            path = _constraint_glyph_path(text if text in (
                "horizontal", "vertical", "coincident", "parallel", "perpendicular",
                "equal", "tangent", "fixed", "concentric", "midpoint") else "coincident")
            # Map short labels back if needed
            label_to_type = {
                "H": "horizontal", "V": "vertical", "C": "coincident", "//": "parallel",
                "⊥": "perpendicular", "=": "equal", "T": "tangent", "F": "fixed",
                "◎": "concentric", "M": "midpoint",
            }
            ctype = label_to_type.get(text, text)
            path = _constraint_glyph_path(ctype)
            item = QGraphicsPathItem(path)
            item.setPen(QPen(QColor(140, 220, 140), 1.4))
            item.setBrush(QBrush(QColor(140, 220, 140, 40)))
            item.setPos(x, y)
        else:
            item = QGraphicsTextItem(text)
            item.setPos(x, y - 6)
            item.setDefaultTextColor(QColor(255, 220, 100))
            item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        item.setZValue(20)
        item.setToolTip(tooltip)
        item.setData(1, "badge")
        item.setData(2, badge_type)
        item.setData(3, badge_index)
        item.setData(4, related_ids or [])
        item.setData(5, (x, y))
        # Store group_id for ordinate group move-together
        if badge_type == "dimension" and self.sketch and 0 <= badge_index < len(self.sketch.dimensions):
            params = self.sketch.dimensions[badge_index].get("parameters") or {}
            gid = params.get("group_id")
            if gid:
                item.setData(6, gid)
        self.scene.addItem(item)


    def _set_badge_color(self, badge: QGraphicsItem, highlight: bool) -> None:
        """Set normal or highlight color on a badge (text or path)."""
        is_dim = badge.data(2) == "dimension"
        if isinstance(badge, QGraphicsTextItem):
            color = QColor(255, 255, 180) if highlight else (
                QColor(255, 220, 100) if is_dim else QColor(140, 220, 140)
            )
            badge.setDefaultTextColor(color)
        elif isinstance(badge, QGraphicsPathItem):
            color = QColor(255, 255, 180) if highlight else QColor(140, 220, 140)
            badge.setPen(QPen(color, 1.6 if highlight else 1.4))
            badge.setBrush(QBrush(color if highlight else QColor(140, 220, 140, 40)))

    def _badge_at(self, pos: QPointF) -> Optional[QGraphicsItem]:
        """Return the badge item under the scene position, if any."""
        for item in self.scene.items(pos):
            if item.data(1) == "badge":
                return item
        return None

    def mouseDoubleClickEvent(self, event):
        """Double-click a dimension badge to start in-place edit."""
        if self.sketch is None or event.button() != Qt.MouseButton.LeftButton:
            return super().mouseDoubleClickEvent(event)
        pos = self.mapToScene(event.position().toPoint())
        badge = self._badge_at(pos)
        if badge is None or badge.data(2) != "dimension":
            return super().mouseDoubleClickEvent(event)
        badge.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        badge.setFocus(Qt.FocusReason.MouseFocusReason)
        cursor = badge.textCursor()
        cursor.select(cursor.SelectionType.Document)
        badge.setTextCursor(cursor)
        return

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

        # Badge interaction: click selects related entities; prepare drag
        badge = self._badge_at(pos)
        if badge is not None:
            related = badge.data(4) or []
            if isinstance(related, list):
                self.selected_ids = set(related)
                self.selected_id = related[0] if related else None
                self._related_ids = set(related)
            self._dragging_badge = badge
            self._badge_drag_start = pos
            self._badge_orig_pos = badge.pos()
            # Collect group badges for move-together (ordinate groups)
            self._dragging_group_badges = []
            gid = badge.data(6)
            if gid:
                for item in self.scene.items():
                    if item.data(1) == "badge" and item.data(6) == gid:
                        self._dragging_group_badges.append(item)
            # Do not refresh here so items remain valid for live drag
            return

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

    def _snap_ordinate_badge(self, badge: QGraphicsItem, proposed: QPointF) -> QPointF:
        """Snap ordinate dimension badge so its leader stays axis-aligned.

        For axis='x' ordinate, snap Y to the origin Y (horizontal leader).
        For axis='y', snap X to the origin X (vertical leader).
        Also snap to nearby group mates for stacked alignment.
        """
        if self.sketch is None or badge.data(2) != "dimension":
            return proposed
        idx = badge.data(3)
        if not isinstance(idx, int) or not (0 <= idx < len(self.sketch.dimensions)):
            return proposed
        dim = self.sketch.dimensions[idx]
        if dim.get("type") != "ordinate":
            return proposed
        params = dim.get("parameters") or {}
        axis = params.get("axis", "x")
        origin = params.get("origin") or [0.0, 0.0]
        if not isinstance(origin, (list, tuple)) or len(origin) < 2:
            origin = [0.0, 0.0]
        ox, oy = float(origin[0]), float(origin[1])
        snap_tol = 6.0
        sx, sy = proposed.x(), proposed.y()

        # Primary axis-aligned snap to origin
        if axis == "x":
            if abs(sy - oy) < snap_tol:
                sy = oy
        elif axis == "y":
            if abs(sx - ox) < snap_tol:
                sx = ox

        # Snap to other group members for stacked alignment
        gid = badge.data(6)
        if gid:
            for item in self.scene.items():
                if item is badge or item.data(1) != "badge" or item.data(6) != gid:
                    continue
                oidx = item.data(3)
                if not isinstance(oidx, int) or not (0 <= oidx < len(self.sketch.dimensions)):
                    continue
                odim = self.sketch.dimensions[oidx]
                if odim.get("type") != "ordinate":
                    continue
                oparams = odim.get("parameters") or {}
                oaxis = oparams.get("axis", "x")
                if oaxis != axis:
                    continue
                op = item.pos()
                if axis == "x" and abs(sy - op.y()) < snap_tol:
                    sy = op.y()
                elif axis == "y" and abs(sx - op.x()) < snap_tol:
                    sx = op.x()

        return QPointF(sx, sy)

        if self.sketch is None:
            return super().mouseMoveEvent(event)
        pos = self.mapToScene(event.position().toPoint())

        # Drag badge to reposition (and group if ordinate)
        if self._dragging_badge is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if self._badge_drag_start is not None and self._badge_orig_pos is not None:
                delta = pos - self._badge_drag_start
                proposed = self._badge_orig_pos + delta
                snapped = self._snap_ordinate_badge(self._dragging_badge, proposed)
                self._dragging_badge.setPos(snapped)
                # Move all group badges by the same delta (relative)
                for gbadge in self._dragging_group_badges:
                    if gbadge is not self._dragging_badge and gbadge.scene() is not None:
                        base = gbadge.data(5)
                        if isinstance(base, tuple) and len(base) == 2:
                            g_proposed = QPointF(base[0], base[1]) + delta
                            gbadge.setPos(self._snap_ordinate_badge(gbadge, g_proposed))
                        else:
                            gbadge.setPos(gbadge.pos() + delta)  # fallback
            return

        # Hover highlight on badges + related entities
        badge = self._badge_at(pos)
        new_related = set()
        if badge is not None:
            rel = badge.data(4) or []
            if isinstance(rel, list):
                new_related = set(rel)
            # Brighten badge color
            if badge is not self._hovered_badge:
                if self._hovered_badge is not None:
                    self._set_badge_color(self._hovered_badge, highlight=False)
                self._set_badge_color(badge, highlight=True)
                self._hovered_badge = badge
        else:
            if self._hovered_badge is not None:
                self._set_badge_color(self._hovered_badge, highlight=False)
                self._hovered_badge = None
        if new_related != self._related_ids:
            self._related_ids = new_related
            self.refresh()

        if self.mode == "select" and self._drag_entity and event.buttons() & Qt.MouseButton.LeftButton:
            # Simple drag for points
            ent = self.sketch.get_entity(self._drag_entity)
            if ent and ent["type"] == "point":
                self.sketch.update_point(self._drag_entity, pos.x(), pos.y())
                self.refresh()
                self.sketch_changed.emit()
            return

        if self.mode == "select" and self._box_start is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._update_box(self._box_start, pos)
            return

        # Live preview for drawing modes
        self._clear_preview()
        if self.mode == "line" and self._start_point:
            start = self.sketch.get_entity(self._start_point)
            if start:
                self._preview_item = self.scene.addLine(start["x"], start["y"], pos.x(), pos.y(),
                                                         QPen(QColor(100, 200, 255), 1, Qt.PenStyle.DashLine))
        elif self.mode == "circle" and self._start_point:
            center = self.sketch.get_entity(self._start_point)
            if center:
                r = math.hypot(pos.x() - center["x"], pos.y() - center["y"])
                self._preview_item = self.scene.addEllipse(center["x"] - r, center["y"] - r, r * 2, r * 2,
                                                            QPen(QColor(100, 200, 255), 1, Qt.PenStyle.DashLine))
        elif self.mode == "rectangle" and self._start_point:
            start = self.sketch.get_entity(self._start_point)
            if start:
                x1, y1 = start["x"], start["y"]
                x2, y2 = pos.x(), pos.y()
                pen = QPen(QColor(100, 200, 255), 1, Qt.PenStyle.DashLine)
                self._preview_item = self.scene.addRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1), pen)
        elif self.mode == "arc" and self._arc_center is not None:
            c = self.sketch.get_entity(self._arc_center)
            if c:
                if self._arc_radius == 0.0:
                    r = math.hypot(pos.x() - c["x"], pos.y() - c["y"])
                    self._preview_item = self.scene.addEllipse(c["x"] - r, c["y"] - r, r * 2, r * 2,
                                                                QPen(QColor(100, 200, 255), 1, Qt.PenStyle.DashLine))
                else:
                    ea = math.degrees(math.atan2(pos.y() - c["y"], pos.x() - c["x"]))
                    path = self._arc_path(c["x"], c["y"], self._arc_radius, self._arc_start_angle, ea)
                    self._preview_item = self.scene.addPath(path, QPen(QColor(100, 200, 255), 1, Qt.PenStyle.DashLine))

    def mouseReleaseEvent(self, event):
        if self.sketch is None or event.button() != Qt.MouseButton.LeftButton:
            return super().mouseReleaseEvent(event)
        pos = self.mapToScene(event.position().toPoint())

        # Commit badge drag offset into parameters
        if self._dragging_badge is not None:
            badge = self._dragging_badge
            btype = badge.data(2)
            idx = badge.data(3)
            # Use the final snapped position for the offset delta
            final_pos = badge.pos()
            delta_dx, delta_dy = 0.0, 0.0
            if self._badge_orig_pos is not None:
                delta_dx = final_pos.x() - self._badge_orig_pos.x()
                delta_dy = final_pos.y() - self._badge_orig_pos.y()
            # Apply to the dragged badge
            if isinstance(idx, int) and idx >= 0 and self.sketch:
                obj = None
                if btype == "constraint" and idx < len(self.sketch.constraints):
                    obj = self.sketch.constraints[idx]
                elif btype == "dimension" and idx < len(self.sketch.dimensions):
                    obj = self.sketch.dimensions[idx]
                if obj is not None:
                    cur_off = self._get_badge_offset(obj)
                    self._set_badge_offset(obj, cur_off[0] + delta_dx, cur_off[1] + delta_dy)
                    self.sketch.validate()
            # Move-together: apply same delta to all other badges in the ordinate group
            gid = badge.data(6)
            if gid and self.sketch:
                for i, dim in enumerate(self.sketch.dimensions):
                    if i == idx:
                        continue
                    params = dim.get("parameters") or {}
                    if params.get("group_id") == gid:
                        cur_off = self._get_badge_offset(dim)
                        self._set_badge_offset(dim, cur_off[0] + delta_dx, cur_off[1] + delta_dy)
                self.sketch.validate()
            self._dragging_badge = None
            self._badge_drag_start = None
            self._badge_orig_pos = None
            self._dragging_group_badges = []
            self.refresh()
            self.sketch_changed.emit()
            return

        # Commit in-place dimension edit if a dimension badge had focus
        for item in list(self.scene.items()):
            if isinstance(item, QGraphicsTextItem) and item.data(1) == "badge" and item.data(2) == "dimension":
                if item.hasFocus():
                    idx = item.data(3)
                    if isinstance(idx, int) and 0 <= idx < len(self.sketch.dimensions):
                        new_text = item.toPlainText().strip()
                        if ":" in new_text:
                            new_text = new_text.split(":", 1)[1].strip()
                        if new_text:
                            self.sketch.dimensions[idx]["value"] = new_text
                            self.sketch.validate()
                            self.sketch_changed.emit()
                    item.clearFocus()

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
            center = self.sketch.get_entity(self._start_point)
            if center:
                r = math.hypot(pos.x() - center["x"], pos.y() - center["y"])
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
                # Create 4 points + 4 lines
                p_br = self._find_or_add_point(QPointF(x2, y1))
                p_tr = self._find_or_add_point(QPointF(x2, y2))
                p_tl = self._find_or_add_point(QPointF(x1, y2))
                self.sketch.add_line(self._start_point, p_br)
                self.sketch.add_line(p_br, p_tr)
                self.sketch.add_line(p_tr, p_tl)
                self.sketch.add_line(p_tl, self._start_point)
                self.sketch.validate()
                self.refresh()
                self.sketch_changed.emit()
            self._start_point = None
            return

        if self.mode == "arc" and self._arc_center is not None:
            # already handled in press for third click; nothing on release
            pass

        super().mouseReleaseEvent(event)

    def _hit_test(self, pos: QPointF) -> Optional[str]:
        """Return entity id under the point, preferring points."""
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
            return math.hypot(pos.x() - ent["x"], pos.y() - ent["y"])
        if etype == "line":
            s = self.sketch.get_entity(ent["start_point"])
            e = self.sketch.get_entity(ent["end_point"])
            if s and e:
                return self._point_to_segment(pos, s["x"], s["y"], e["x"], e["y"])
        if etype in ("circle", "arc"):
            c = self.sketch.get_entity(ent["center"])
            if c:
                return abs(math.hypot(pos.x() - c["x"], pos.y() - c["y"]) - ent["radius"])
        return None

    @staticmethod
    def _point_to_segment(p: QPointF, x1: float, y1: float, x2: float, y2: float) -> float:
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(p.x() - x1, p.y() - y1)
        t = max(0, min(1, ((p.x() - x1) * dx + (p.y() - y1) * dy) / (dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(p.x() - proj_x, p.y() - proj_y)

    def _update_box(self, start: QPointF, end: QPointF) -> None:
        self._clear_box()
        rect = QRectF(start, end).normalized()
        pen = QPen(QColor(100, 180, 255), 1, Qt.PenStyle.DashLine)
        brush = QBrush(QColor(100, 180, 255, 40))
        self._box_item = self.scene.addRect(rect, pen, brush)
        self._box_item.setZValue(30)

    def _finish_box_select(self, start: QPointF, end: QPointF) -> None:
        rect = QRectF(start, end).normalized()
        self.selected_ids.clear()
        for ent in self.sketch.entities:
            if self._entity_in_rect(ent, rect):
                self.selected_ids.add(ent["id"])
        self.selected_id = next(iter(self.selected_ids), None)

    def _entity_in_rect(self, ent: dict, rect: QRectF) -> bool:
        etype = ent["type"]
        if etype == "point":
            return rect.contains(QPointF(ent["x"], ent["y"]))
        if etype == "line":
            s = self.sketch.get_entity(ent["start_point"])
            e = self.sketch.get_entity(ent["end_point"])
            if s and e:
                return self._segment_intersects_rect(s["x"], s["y"], e["x"], e["y"], rect)
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
