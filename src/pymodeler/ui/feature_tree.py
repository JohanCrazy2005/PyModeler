"""Feature tree / timeline UI for PyModeler.

Displays FeatureHistory items, property panel, visual suppression after rollback marker,
and context menu to set the rollback marker.
"""

from __future__ import annotations

from typing import Optional, Union

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pymodeler.core import (
    ChamferFeature,
    ExtrudeFeature,
    FeatureHistory,
    FilletFeature,
    HoleFeature,
    ParameterStore,
    RevolveFeature,
    ShellFeature,
)


class FeatureTreeWidget(QListWidget):
    """List showing features from a FeatureHistory with rollback support."""

    feature_selected = pyqtSignal(object)  # feature or None
    rollback_changed = pyqtSignal()  # emitted when marker is set

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.history: Optional[FeatureHistory] = None
        self.itemSelectionChanged.connect(self._on_selection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_history(self, history: FeatureHistory) -> None:
        self.history = history
        self.refresh()

    def refresh(self) -> None:
        self.blockSignals(True)
        self.clear()
        if self.history is not None:
            active = self.history.get_active_count()
            for i, fdict in enumerate(self.history.features):
                name = fdict.get("name", fdict.get("type", "Feature"))
                ftype = fdict.get("type", "?")
                text = f"{name} ({ftype})"
                item = QListWidgetItem(text)
                # Store index and dict
                item.setData(Qt.ItemDataRole.UserRole, i)
                if i >= active:
                    item.setText(f"{text} [suppressed]")
                    item.setForeground(QColor(140, 140, 140))
                self.addItem(item)
        self.blockSignals(False)

    def _on_selection(self) -> None:
        items = self.selectedItems()
        if items and self.history is not None:
            idx = items[0].data(Qt.ItemDataRole.UserRole)
            fdict = self.history.features[idx]
            ftype = fdict.get("type")
            if ftype == "extrude":
                feat = ExtrudeFeature.from_dict(fdict)
            elif ftype == "revolve":
                feat = RevolveFeature.from_dict(fdict)
            elif ftype == "hole":
                feat = HoleFeature.from_dict(fdict)
            elif ftype == "fillet":
                feat = FilletFeature.from_dict(fdict)
            elif ftype == "chamfer":
                feat = ChamferFeature.from_dict(fdict)
            elif ftype == "shell":
                feat = ShellFeature.from_dict(fdict)
            else:
                feat = None
            self.feature_selected.emit(feat)
        else:
            self.feature_selected.emit(None)

    def _show_context_menu(self, pos) -> None:
        if self.history is None:
            return
        item = self.itemAt(pos)
        menu = QMenu(self)
        if item is not None:
            idx = item.data(Qt.ItemDataRole.UserRole)
            roll_here = QAction(f"Roll to here (after feature {idx + 1})", self)
            roll_here.triggered.connect(lambda: self._set_rollback(idx + 1))
            menu.addAction(roll_here)
        roll_end = QAction("Roll to end (all active)", self)
        roll_end.triggered.connect(lambda: self._set_rollback(None))
        menu.addAction(roll_end)
        menu.exec(self.mapToGlobal(pos))

    def _set_rollback(self, index: Optional[int]) -> None:
        if self.history is None:
            return
        self.history.set_rollback(index)
        self.refresh()
        self.rollback_changed.emit()


class PropertyPanel(QWidget):
    """Simple property editor for Extrude / Revolve / Hole / Fillet / Chamfer / Shell features."""

    properties_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Properties"))

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(self._apply)
        form.addRow("Name:", self.name_edit)

        self.distance_edit = QLineEdit()
        self.distance_edit.setPlaceholderText("number or parameter name")
        self.distance_edit.editingFinished.connect(self._apply)
        form.addRow("Distance / Angle / Diameter / Radius / Thickness:", self.distance_edit)

        self.offset_edit = QLineEdit()
        self.offset_edit.setPlaceholderText("start offset (extrude), depth (hole), distance2 or angle (chamfer)")
        self.offset_edit.editingFinished.connect(self._apply)
        form.addRow("Offset / Depth / Secondary:", self.offset_edit)

        self.direction_edit = QLineEdit()
        self.direction_edit.setPlaceholderText("x,y,z (hole direction) or inside/outside/both (shell)")
        self.direction_edit.editingFinished.connect(self._apply)
        form.addRow("Direction:", self.direction_edit)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["equal_distance", "two_distance", "distance_angle"])
        self.mode_combo.currentTextChanged.connect(self._apply)
        form.addRow("Chamfer Mode:", self.mode_combo)

        self.selection_edit = QLineEdit()
        self.selection_edit.setPlaceholderText("comma-separated edge/face indices or IDs (e.g. 0,1,3 or e1,e2)")
        self.selection_edit.editingFinished.connect(self._apply)
        form.addRow("Edges / Faces:", self.selection_edit)

        self.sketch_label = QLabel()
        form.addRow("Sketch ID:", self.sketch_label)

        layout.addLayout(form)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply)
        layout.addWidget(self.apply_btn)
        layout.addStretch()

        self.current_feature: Optional[
            Union[
                ExtrudeFeature,
                RevolveFeature,
                HoleFeature,
                FilletFeature,
                ChamferFeature,
                ShellFeature,
            ]
        ] = None
        self.history: Optional[FeatureHistory] = None
        self.parameters: Optional[ParameterStore] = None

    def set_context(
        self,
        history: Optional[FeatureHistory],
        parameters: Optional[ParameterStore],
    ) -> None:
        self.history = history
        self.parameters = parameters

    def show_feature(
        self,
        feature: Optional[
            Union[
                ExtrudeFeature,
                RevolveFeature,
                HoleFeature,
                FilletFeature,
                ChamferFeature,
                ShellFeature,
            ]
        ],
    ) -> None:
        self.current_feature = feature
        if feature is None:
            self.name_edit.clear()
            self.distance_edit.clear()
            self.offset_edit.clear()
            self.direction_edit.clear()
            self.selection_edit.clear()
            self.sketch_label.clear()
            self.mode_combo.setEnabled(False)
            self.selection_edit.setEnabled(False)
            self.setEnabled(False)
            return
        self.setEnabled(True)
        self.name_edit.setText(feature.name)
        self.direction_edit.setEnabled(False)
        self.direction_edit.clear()
        self.offset_edit.setEnabled(False)
        self.offset_edit.clear()
        self.mode_combo.setEnabled(False)
        self.mode_combo.setCurrentText("equal_distance")
        self.selection_edit.setEnabled(False)
        self.selection_edit.clear()

        if isinstance(feature, ExtrudeFeature):
            dist = feature.distance
            self.distance_edit.setText(str(dist) if not isinstance(dist, str) else dist)
            off = feature.start_offset
            self.offset_edit.setText(str(off) if not isinstance(off, str) else str(off))
            self.offset_edit.setEnabled(True)
            self.sketch_label.setText(feature.sketch_id)
        elif isinstance(feature, RevolveFeature):
            ang = feature.angle
            self.distance_edit.setText(str(ang) if not isinstance(ang, str) else ang)
            self.sketch_label.setText(feature.sketch_id)
        elif isinstance(feature, HoleFeature):
            diam = feature.diameter
            self.distance_edit.setText(str(diam) if not isinstance(diam, str) else diam)
            dep = feature.depth
            self.offset_edit.setText(str(dep) if not isinstance(dep, str) else str(dep))
            self.offset_edit.setEnabled(True)
            if feature.direction:
                self.direction_edit.setText(
                    ",".join(str(c) for c in feature.direction)
                )
            self.direction_edit.setEnabled(True)
            self.sketch_label.setText("(none)")
        elif isinstance(feature, FilletFeature):
            rad = feature.radius
            self.distance_edit.setText(str(rad) if not isinstance(rad, str) else rad)
            self.selection_edit.setText(",".join(str(e) for e in feature.edges))
            self.selection_edit.setEnabled(True)
            self.sketch_label.setText("(none)")
        elif isinstance(feature, ChamferFeature):
            dist = feature.distance
            self.distance_edit.setText(str(dist) if not isinstance(dist, str) else dist)
            self.mode_combo.setEnabled(True)
            self.mode_combo.setCurrentText(feature.mode or "equal_distance")
            if feature.distance2 is not None:
                d2 = feature.distance2
                self.offset_edit.setText(str(d2) if not isinstance(d2, str) else d2)
                self.offset_edit.setEnabled(True)
            elif feature.angle is not None:
                ang = feature.angle
                self.offset_edit.setText(str(ang) if not isinstance(ang, str) else ang)
                self.offset_edit.setEnabled(True)
            self.selection_edit.setText(",".join(str(e) for e in feature.edges))
            self.selection_edit.setEnabled(True)
            self.sketch_label.setText("(none)")
        elif isinstance(feature, ShellFeature):
            thick = feature.thickness
            self.distance_edit.setText(str(thick) if not isinstance(thick, str) else thick)
            self.direction_edit.setText(feature.direction or "inside")
            self.direction_edit.setEnabled(True)
            self.selection_edit.setText(",".join(str(f) for f in feature.faces))
            self.selection_edit.setEnabled(True)
            self.sketch_label.setText("(none)")
        else:
            self.sketch_label.setText("")

    def _apply(self) -> None:
        if self.current_feature is None or self.history is None:
            return
        name = self.name_edit.text().strip() or self.current_feature.type.capitalize()
        dist_text = self.distance_edit.text().strip()
        try:
            value: float | str = float(dist_text)
        except ValueError:
            value = dist_text or "0"

        for i, fdict in enumerate(self.history.features):
            if fdict.get("id") == self.current_feature.id:
                self.current_feature.name = name
                if isinstance(self.current_feature, ExtrudeFeature):
                    self.current_feature.distance = value
                    off_text = self.offset_edit.text().strip()
                    try:
                        off: float | str = float(off_text) if off_text else 0.0
                    except ValueError:
                        off = off_text or 0.0
                    self.current_feature.start_offset = off
                elif isinstance(self.current_feature, RevolveFeature):
                    self.current_feature.angle = value
                elif isinstance(self.current_feature, HoleFeature):
                    self.current_feature.diameter = value
                    dep_text = self.offset_edit.text().strip()
                    try:
                        dep: float | str = float(dep_text) if dep_text else 1.0
                    except ValueError:
                        dep = dep_text or 1.0
                    self.current_feature.depth = dep
                    dir_text = self.direction_edit.text().strip()
                    if dir_text:
                        try:
                            parts = [float(p.strip()) for p in dir_text.split(",")]
                            if len(parts) == 3:
                                self.current_feature.direction = parts
                            else:
                                self.current_feature.direction = None
                        except ValueError:
                            self.current_feature.direction = None
                    else:
                        self.current_feature.direction = None
                elif isinstance(self.current_feature, FilletFeature):
                    self.current_feature.radius = value
                    self.current_feature.edges = self._parse_selection(self.selection_edit.text())
                elif isinstance(self.current_feature, ChamferFeature):
                    self.current_feature.distance = value
                    self.current_feature.mode = self.mode_combo.currentText()
                    sec_text = self.offset_edit.text().strip()
                    if self.current_feature.mode == "two_distance":
                        try:
                            self.current_feature.distance2 = float(sec_text) if sec_text else None
                        except ValueError:
                            self.current_feature.distance2 = sec_text or None
                        self.current_feature.angle = None
                    elif self.current_feature.mode == "distance_angle":
                        try:
                            self.current_feature.angle = float(sec_text) if sec_text else None
                        except ValueError:
                            self.current_feature.angle = sec_text or None
                        self.current_feature.distance2 = None
                    else:
                        self.current_feature.distance2 = None
                        self.current_feature.angle = None
                    self.current_feature.edges = self._parse_selection(self.selection_edit.text())
                elif isinstance(self.current_feature, ShellFeature):
                    self.current_feature.thickness = value
                    dir_text = self.direction_edit.text().strip().lower()
                    if dir_text in ("inside", "outside", "both"):
                        self.current_feature.direction = dir_text
                    else:
                        self.current_feature.direction = "inside"
                    self.current_feature.faces = self._parse_selection(self.selection_edit.text())
                self.history.features[i] = self.current_feature.to_dict()
                self.history.validate()
                break
        self.properties_changed.emit()

    def _parse_selection(self, text: str) -> list:
        """Parse comma-separated edge/face selectors into a list of int or str."""
        result = []
        for part in text.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                result.append(int(part))
            except ValueError:
                result.append(part)
        return result

    def apply_viewport_selection(self, mode: str, indices: list) -> None:
        """Fill the Edges/Faces field from a viewport pick (when a suitable feature is active)."""
        if self.current_feature is None:
            return
        from pymodeler.core import FilletFeature, ChamferFeature, ShellFeature
        if mode == "edge" and isinstance(self.current_feature, (FilletFeature, ChamferFeature)):
            self.selection_edit.setText(",".join(str(i) for i in indices))
            self.selection_edit.setEnabled(True)
        elif mode == "face" and isinstance(self.current_feature, ShellFeature):
            self.selection_edit.setText(",".join(str(i) for i in indices))
            self.selection_edit.setEnabled(True)

