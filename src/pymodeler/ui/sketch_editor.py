"""Basic 2D sketch editor widget (table-based stub).

Allows creating and editing sketch entities and dimensions connected to the Sketch data model.
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
    QDoubleSpinBox,
    QComboBox,
    QMessageBox,
)

from pymodeler.core import Sketch, create_rectangle_sketch


class SketchEditorWidget(QWidget):
    """Table-based editor for a Sketch: entities, constraints, dimensions."""

    sketch_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.sketch: Optional[Sketch] = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sketch Editor"))

        self.tabs = QTabWidget()
        self.entities_table = self._make_entities_table()
        self.constraints_table = self._make_simple_table(["ID", "Type", "Entities"])
        self.dimensions_table = self._make_simple_table(["ID", "Type", "Value", "Entities", "Driven"])

        self.tabs.addTab(self.entities_table, "Entities")
        self.tabs.addTab(self.constraints_table, "Constraints")
        self.tabs.addTab(self.dimensions_table, "Dimensions")
        layout.addWidget(self.tabs)

        # Add controls
        btn_layout = QHBoxLayout()
        self.add_point_btn = QPushButton("Add Point")
        self.add_point_btn.clicked.connect(self._add_point)
        btn_layout.addWidget(self.add_point_btn)

        self.add_line_btn = QPushButton("Add Line")
        self.add_line_btn.clicked.connect(self._add_line)
        btn_layout.addWidget(self.add_line_btn)

        self.add_circle_btn = QPushButton("Add Circle")
        self.add_circle_btn.clicked.connect(self._add_circle)
        btn_layout.addWidget(self.add_circle_btn)

        self.add_rect_btn = QPushButton("Add Rectangle")
        self.add_rect_btn.clicked.connect(self._add_rectangle)
        btn_layout.addWidget(self.add_rect_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

        # Dimension add
        dim_layout = QHBoxLayout()
        self.dim_type = QComboBox()
        self.dim_type.addItems(["length", "radius", "distance"])
        dim_layout.addWidget(self.dim_type)
        self.dim_value = QLineEdit()
        self.dim_value.setPlaceholderText("value or param")
        dim_layout.addWidget(self.dim_value)
        self.add_dim_btn = QPushButton("Add Dimension")
        self.add_dim_btn.clicked.connect(self._add_dimension)
        dim_layout.addWidget(self.add_dim_btn)
        layout.addLayout(dim_layout)

        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(self._update_name)
        form = QFormLayout()
        form.addRow("Sketch Name:", self.name_edit)
        layout.addLayout(form)

        self.setEnabled(False)

    def _make_entities_table(self) -> QTableWidget:
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Type", "ID", "Details", "Construction", "Fixed"])
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        return table

    def _make_simple_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        return table

    def set_sketch(self, sketch: Optional[Sketch]) -> None:
        self.sketch = sketch
        self.setEnabled(sketch is not None)
        self.refresh()

    def refresh(self) -> None:
        if self.sketch is None:
            self.entities_table.setRowCount(0)
            self.constraints_table.setRowCount(0)
            self.dimensions_table.setRowCount(0)
            self.name_edit.clear()
            return

        self.name_edit.setText(self.sketch.name)

        # Entities
        self.entities_table.setRowCount(len(self.sketch.entities))
        for row, ent in enumerate(self.sketch.entities):
            self.entities_table.setItem(row, 0, QTableWidgetItem(ent["type"]))
            self.entities_table.setItem(row, 1, QTableWidgetItem(ent["id"]))
            details = ""
            if ent["type"] == "point":
                details = f"({ent['x']:.2f}, {ent['y']:.2f})"
            elif ent["type"] == "line":
                details = f"{ent['start_point'][:8]} → {ent['end_point'][:8]}"
            elif ent["type"] == "circle":
                details = f"r={ent['radius']:.2f} @ {ent['center'][:8]}"
            elif ent["type"] == "arc":
                details = f"r={ent['radius']:.2f} {ent['start_angle']:.1f}-{ent['end_angle']:.1f}"
            self.entities_table.setItem(row, 2, QTableWidgetItem(details))
            self.entities_table.setItem(row, 3, QTableWidgetItem(str(ent.get("construction", False))))
            self.entities_table.setItem(row, 4, QTableWidgetItem(str(ent.get("fixed", False))))

        # Constraints
        self.constraints_table.setRowCount(len(self.sketch.constraints))
        for row, con in enumerate(self.sketch.constraints):
            self.constraints_table.setItem(row, 0, QTableWidgetItem(con["id"]))
            self.constraints_table.setItem(row, 1, QTableWidgetItem(con["type"]))
            self.constraints_table.setItem(row, 2, QTableWidgetItem(", ".join(con["entities"])))

        # Dimensions
        self.dimensions_table.setRowCount(len(self.sketch.dimensions))
        for row, dim in enumerate(self.sketch.dimensions):
            self.dimensions_table.setItem(row, 0, QTableWidgetItem(dim["id"]))
            self.dimensions_table.setItem(row, 1, QTableWidgetItem(dim["type"]))
            self.dimensions_table.setItem(row, 2, QTableWidgetItem(str(dim["value"])))
            self.dimensions_table.setItem(row, 3, QTableWidgetItem(", ".join(dim["entities"])))
            self.dimensions_table.setItem(row, 4, QTableWidgetItem(str(dim.get("driven", False))))

    def _add_point(self) -> None:
        if self.sketch is None:
            return
        # Default position; user can later edit via table if we add editing
        self.sketch.add_point(0.0, 0.0)
        self.refresh()
        self.sketch_changed.emit()

    def _add_line(self) -> None:
        if self.sketch is None:
            return
        points = self.sketch.entity_ids_by_type("point")
        if len(points) < 2:
            QMessageBox.warning(self, "Need Points", "Add at least two points first.")
            return
        self.sketch.add_line(points[0], points[1])
        self.refresh()
        self.sketch_changed.emit()

    def _add_circle(self) -> None:
        if self.sketch is None:
            return
        points = self.sketch.entity_ids_by_type("point")
        if not points:
            QMessageBox.warning(self, "Need Point", "Add a center point first.")
            return
        self.sketch.add_circle(points[0], 5.0)
        self.refresh()
        self.sketch_changed.emit()

    def _add_rectangle(self) -> None:
        if self.sketch is None:
            return
        # Append a rectangle's entities/constraints/dims to current sketch
        rect = create_rectangle_sketch(width=10.0, height=5.0, name="Rect")
        for ent in rect.entities:
            self.sketch.entities.append(ent)
        for con in rect.constraints:
            self.sketch.constraints.append(con)
        for dim in rect.dimensions:
            self.sketch.dimensions.append(dim)
        self.sketch.validate()
        self.refresh()
        self.sketch_changed.emit()

    def _add_dimension(self) -> None:
        if self.sketch is None:
            return
        dtype = self.dim_type.currentText()
        val_text = self.dim_value.text().strip() or "1.0"
        try:
            value: float | str = float(val_text)
        except ValueError:
            value = val_text

        if dtype == "length":
            lines = self.sketch.entity_ids_by_type("line")
            if not lines:
                QMessageBox.warning(self, "Need Line", "Add a line first.")
                return
            self.sketch.add_length_dimension(lines[0], value)
        elif dtype == "radius":
            circles = self.sketch.entity_ids_by_type("circle")
            if not circles:
                QMessageBox.warning(self, "Need Circle", "Add a circle first.")
                return
            self.sketch.add_radius_dimension(circles[0], value)
        else:
            points = self.sketch.entity_ids_by_type("point")
            if len(points) < 2:
                QMessageBox.warning(self, "Need Points", "Need two points for distance.")
                return
            self.sketch.add_distance_dimension(points[0], points[1], value)

        self.refresh()
        self.sketch_changed.emit()

    def _delete_selected(self) -> None:
        if self.sketch is None:
            return
        current = self.tabs.currentWidget()
        if current == self.entities_table:
            rows = sorted({idx.row() for idx in self.entities_table.selectedIndexes()}, reverse=True)
            for r in rows:
                if 0 <= r < len(self.sketch.entities):
                    del self.sketch.entities[r]
        elif current == self.constraints_table:
            rows = sorted({idx.row() for idx in self.constraints_table.selectedIndexes()}, reverse=True)
            for r in rows:
                if 0 <= r < len(self.sketch.constraints):
                    del self.sketch.constraints[r]
        elif current == self.dimensions_table:
            rows = sorted({idx.row() for idx in self.dimensions_table.selectedIndexes()}, reverse=True)
            for r in rows:
                if 0 <= r < len(self.sketch.dimensions):
                    del self.sketch.dimensions[r]
        try:
            self.sketch.validate()
        except Exception:
            # If invalid after delete (dangling refs), user can fix; keep going for stub
            pass
        self.refresh()
        self.sketch_changed.emit()

    def _update_name(self) -> None:
        if self.sketch is not None:
            self.sketch.name = self.name_edit.text().strip() or "Sketch"
            self.sketch.validate()
            self.sketch_changed.emit()
