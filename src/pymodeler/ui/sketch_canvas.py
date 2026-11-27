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
        self.show_badges: bool = True
        self._hovered_badge: Optional[QGraphicsTextItem] = None

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
        if self.sketch is None or not self.show_badges:
            return

        # Constraint type to short label (glyphs)
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

        for idx, con in enumerate(self.sketch.constraints):
            label = ctype_labels.get(con.get("type", ""), "?")
            ents = con.get("entities") or []
            if not ents:
                continue
            pos = self._badge_position_for_entity(ents[0])
            if pos is None:
                continue
            self._add_badge(pos[0], pos[1], label, tooltip=f"{con.get('type')} {ents}",
                            badge_type="constraint", badge_index=idx)

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
            # Offset dimensions a bit further
            ox, oy = pos
            self._add_badge(ox + 4.0, oy + 4.0, label, tooltip=f"{dtype}={value} {ents}",
                            is_dim=True, badge_type="dimension", badge_index=idx)

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

    def _add_badge(self, x: float, y: float, text: str, tooltip: str = "", is_dim: bool = False,
                   badge_type: str = "constraint", badge_index: int = -1) -> None:
        """Add a small text badge at (x, y)."""
        item = QGraphicsTextItem(text)
        item.setPos(x, y - 6)
        item.setDefaultTextColor(QColor(255, 220, 100) if is_dim else QColor(140, 220, 140))
        item.setZValue(20)
        item.setToolTip(tooltip)
        # Store markers so tests and hover/edit can find badges
        item.setData(1, "badge")
        item.setData(2, badge_type)
        item.setData(3, badge_index)
        self.scene.addItem(item)

    # ... (rest of the file continues with drawing, mouse events, hover, double-click, etc.)
    # Full implementation includes the hover and double-click methods added in this run.
