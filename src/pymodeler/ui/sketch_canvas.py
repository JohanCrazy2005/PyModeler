"""Minimal sketch canvas widget (QGraphicsView stub).

Provides basic visual representation and mouse drawing hooks so the SketchEditor
can import and function. Full interactive canvas is a later polish item.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget

from pymodeler.core.sketch import Sketch


class SketchCanvasWidget(QGraphicsView):
    """Minimal canvas that holds a Sketch and emits sketch_changed.

    Currently a placeholder scene; real drawing/snapping will be expanded later.
    """

    sketch_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.sketch: Optional[Sketch] = None
        self.setMinimumHeight(200)
        self.setRenderHint(self.RenderHint.Antialiasing, True)

    def set_sketch(self, sketch: Optional[Sketch]) -> None:
        self.sketch = sketch
        self.refresh()

    def refresh(self) -> None:
        """Rebuild scene from current sketch (stub: clear only)."""
        self.scene.clear()
        if self.sketch is None:
            return
        # Future: draw points, lines, circles, arcs, dimensions here.
        # For now just ensure the widget is valid and does not crash.
        pass
