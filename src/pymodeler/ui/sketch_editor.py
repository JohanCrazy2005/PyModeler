"""Basic 2D sketch editor widget (table-based stub).

Allows creating and editing sketch entities and dimensions connected to the Sketch data model.
Supports editable table cells for point coordinates and dimension values.
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
)

from pymodeler.core import Sketch, create_rectangle_sketch


class SketchEditorWidget(QWidget):
    """Table-based editor for a Sketch: entities, constraints, dimensions.

    Entities table is editable for point X/Y and circle radius.
    Dimensions table is editable for values.
    """

    sketch_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.sketch: Optional[Sketch] = None
        self._updating = False  # Guard against recursive itemChanged

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

        # Connect editable signals
        self.entities_table.itemChanged.connect(self._on_entities_item_changed)
        self.dimensions_table.itemChanged.connect(self._on_dimensions_item_changed)

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
        # Columns: Type, ID, X/Param1, Y/Param2, Other, Construction, Fixed
        table = QTableWidget(0, 7)
        table.setHorizontalHeaderLabels(
            ["Type", "ID", "X / Radius", "Y / Angle", "Other", "Construction", "Fixed"]
        )
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)
        return table

    def _make_simple_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)
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

        self._updating = True
        try:
            self.name_edit.setText(self.sketch.name)

            # Entities
            self.entities_table.setRowCount(len(self.sketch.entities))
            for row, ent in enumerate(self.sketch.entities):
                type_item = QTableWidgetItem(ent["type"])
                type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.entities_table.setItem(row, 0, type_item)

                id_item = QTableWidgetItem(ent["id"])
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.entities_table.setItem(row, 1, id_item)

                # Param columns (editable for relevant types)
                x_item = QTableWidgetItem("")
                y_item = QTableWidgetItem("")
                other_item = QTableWidgetItem("")

                if ent["type"] == "point":
                    x_item.setText(f"{ent['x']:.6g}")
                    y_item.setText(f"{ent['y']:.6g}")
                elif ent["type"] == "circle":
                    x_item.setText(f"{ent['radius']:.6g}")
                    other_item.setText(f"center={ent['center'][:8]}")
                elif ent["type"] == "arc":
                    x_item.setText(f"{ent['radius']:.6g}")
                    y_item.setText(f"{ent['start_angle']:.6g}")
                    other_item.setText(f"end={ent['end_angle']:.6g} center={ent['center'][:8]}")
                elif ent["type"] == "line":
                    other_item.setText(f"{ent['start_point'][:8]} → {ent['end_point'][:8]}")

                self.entities_table.setItem(row, 2, x_item)
                self.entities_table.setItem(row, 3, y_item)
                other_item.setFlags(other_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.entities_table.setItem(row, 4, other_item)

                cons_item = QTableWidgetItem(str(ent.get("construction", False)))
                cons_item.setFlags(cons_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.entities_table.setItem(row, 5, cons_item)

                fixed_item = QTableWidgetItem(str(ent.get("fixed", False)))
                fixed_item.setFlags(fixed_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.entities_table.setItem(row, 6, fixed_item)

            # Constraints (read-only for now)
            self.constraints_table.setRowCount(len(self.sketch.constraints))
            for row, con in enumerate(self.sketch.constraints):
                for col, text in enumerate([con["id"], con["type"], ", ".join(con["entities"])]):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.constraints_table.setItem(row, col, item)

            # Dimensions (value editable)
            self.dimensions_table.setRowCount(len(self.sketch.dimensions))
            for row, dim in enumerate(self.sketch.dimensions):
                id_item = QTableWidgetItem(dim["id"])
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.dimensions_table.setItem(row, 0, id_item)

                type_item = QTableWidgetItem(dim["type"])
                type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.dimensions_table.setItem(row, 1, type_item)

                val_item = QTableWidgetItem(str(dim["value"]))
                self.dimensions_table.setItem(row, 2, val_item)

                ents_item = QTableWidgetItem(", ".join(dim["entities"]))
                ents_item.setFlags(ents_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.dimensions_table.setItem(row, 3, ents_item)

                driven_item = QTableWidgetItem(str(dim.get("driven", False)))
                driven_item.setFlags(driven_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.dimensions_table.setItem(row, 4, driven_item)
        finally:
            self._updating = False

    def _on_entities_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating or self.sketch is None:
            return
        row = item.row()
        col = item.column()
        if row < 0 or row >= len(self.sketch.entities):
            return
        ent = self.sketch.entities[row]
        text = item.text().strip()
        try:
            if col == 2:  # X / Radius
                val = float(text)
                if ent["type"] == "point":
                    ent["x"] = val
                elif ent["type"] in ("circle", "arc"):
                    ent["radius"] = max(0.0, val)
            elif col == 3:  # Y / Angle
                val = float(text)
                if ent["type"] == "point":
                    ent["y"] = val
                elif ent["type"] == "arc":
                    ent["start_angle"] = val
            else:
                return
            self.sketch.validate()
            self.sketch_changed.emit()
        except (ValueError, KeyError):
            # Revert by refreshing
            self.refresh()
            QMessageBox.warning(self, "Invalid Value", "Please enter a valid number.")

    def _on_dimensions_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating or self.sketch is None:
            return
        row = item.row()
        col = item.column()
        if col != 2 or row < 0 or row >= len(self.sketch.dimensions):
            return
        dim = self.sketch.dimensions[row]
        text = item.text().strip()
        if not text:
            self.refresh()
            return
        try:
            value: float | str = float(text)
        except ValueError:
            value = text  # allow parameter names
        dim["value"] = value
        try:
            self.sketch.validate()
            self.sketch_changed.emit()
        except Exception:
            self.refresh()
            QMessageBox.warning(self, "Invalid Value", "Dimension value failed validation.")

    def _selected_entity_ids(self, etype: Optional[str] = None) -> list[str]:
        """Return IDs of selected entities (optionally filtered by type)."""
        if self.sketch is None:
            return []
        rows = sorted({idx.row() for idx in self.entities_table.selectedIndexes()})
        ids = []
        for r in rows:
            if 0 <= r < len(self.sketch.entities):
                ent = self.sketch.entities[r]
                if etype is None or ent["type"] == etype:
                    ids.append(ent["id"])
        return ids

    def _add_point(self) -> None:
        if self.sketch is None:
            return
        self.sketch.add_point(0.0, 0.0)
        self.refresh()
        self.sketch_changed.emit()

    def _add_line(self) -> None:
        if self.sketch is None:
            return
        selected_points = self._selected_entity_ids("point")
        if len(selected_points) >= 2:
            start, end = selected_points[0], selected_points[1]
        else:
            points = self.sketch.entity_ids_by_type("point")
            if len(points) < 2:
                QMessageBox.warning(self, "Need Points", "Add or select at least two points first.")
                return
            start, end = points[0], points[1]
        self.sketch.add_line(start, end)
        self.refresh()
        self.sketch_changed.emit()

    def _add_circle(self) -> None:
        if self.sketch is None:
            return
        selected_points = self._selected_entity_ids("point")
        if selected_points:
            center = selected_points[0]
        else:
            points = self.sketch.entity_ids_by_type("point")
            if not points:
                QMessageBox.warning(self, "Need Point", "Add or select a center point first.")
                return
            center = points[0]
        self.sketch.add_circle(center, 5.0)
        self.refresh()
        self.sketch_changed.emit()

    def _add_rectangle(self) -> None:
        if self.sketch is None:
            return
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
            selected_lines = self._selected_entity_ids("line")
            if selected_lines:
                target = selected_lines[0]
            else:
                lines = self.sketch.entity_ids_by_type("line")
                if not lines:
                    QMessageBox.warning(self, "Need Line", "Add or select a line first.")
                    return
                target = lines[0]
            self.sketch.add_length_dimension(target, value)
        elif dtype == "radius":
            selected = self._selected_entity_ids("circle") or self._selected_entity_ids("arc")
            if selected:
                target = selected[0]
            else:
                circles = self.sketch.entity_ids_by_type("circle")
                if not circles:
                    QMessageBox.warning(self, "Need Circle", "Add or select a circle first.")
                    return
                target = circles[0]
            self.sketch.add_radius_dimension(target, value)
        else:
            selected_points = self._selected_entity_ids("point")
            if len(selected_points) >= 2:
                a, b = selected_points[0], selected_points[1]
            else:
                points = self.sketch.entity_ids_by_type("point")
                if len(points) < 2:
                    QMessageBox.warning(self, "Need Points", "Need two points for distance.")
                    return
                a, b = points[0], points[1]
            self.sketch.add_distance_dimension(a, b, value)

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
            pass
        self.refresh()
        self.sketch_changed.emit()

    def _update_name(self) -> None:
        if self.sketch is not None:
            self.sketch.name = self.name_edit.text().strip() or "Sketch"
            self.sketch.validate()
            self.sketch_changed.emit()
