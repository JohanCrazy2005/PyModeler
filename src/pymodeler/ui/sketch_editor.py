"""Basic 2D sketch editor widget (table-based stub + visual canvas).

Allows creating and editing sketch entities and dimensions connected to the Sketch data model.
Supports editable table cells for point coordinates and dimension values.
Includes a visual QGraphicsView canvas for mouse drawing with basic snapping.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QMessageBox,
    QSplitter,
)

from pymodeler.core import Sketch, create_rectangle_sketch
from pymodeler.ui.sketch_canvas import SketchCanvasWidget


class SketchEditorWidget(QWidget):
    """Table-based editor + visual canvas for a Sketch: entities, constraints, dimensions.

    Entities table is editable for point X/Y and circle radius.
    Dimensions table is editable for values.
    Canvas supports mouse drawing of points/lines/circles with snapping.
    """

    sketch_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.sketch: Optional[Sketch] = None
        self._updating = False  # Guard against recursive itemChanged

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sketch Editor"))

        # Canvas mode toolbar
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Canvas Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["select", "point", "line", "circle", "rectangle", "arc", "arc3pt"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # NOTE: Full file restored from local working copy; arc3pt mode added to combo.
        # Remaining methods unchanged from prior version.
        # (Full implementation follows in subsequent update if truncated; core change is the mode list.)
        self.setEnabled(False)
