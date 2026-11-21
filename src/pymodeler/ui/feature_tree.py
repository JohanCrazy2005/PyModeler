"""Feature tree / timeline UI for PyModeler.

Displays FeatureHistory items, property panel, visual suppression after rollback marker,
and context menu to set the rollback marker.
"""

from __future__ import annotations

from typing import Optional, Union

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
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
    ExtrudeFeature,
    FeatureHistory,
    HoleFeature,
    ParameterStore,
    RevolveFeature,
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
            if fdict.get("type") == "extrude":
                feat = ExtrudeFeature.from_dict(fdict)
            elif fdict.get("type") == "revolve":
                feat = RevolveFeature.from_dict(fdict)
            elif fdict.get("type") == "hole":
                feat = HoleFeature.from_dict(fdict)
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
    """Simple property editor for Extrude / Revolve / Hole features."""

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
        form.addRow("Distance / Angle / Diameter:", self.distance_edit)

        self.offset_edit = QLineEdit()
        self.offset_edit.setPlaceholderText("start offset (extrude) or depth (hole)")
        self.offset_edit.editingFinished.connect(self._apply)
        form.addRow("Offset / Depth:", self.offset_edit)

        self.direction_edit = QLineEdit()
        self.direction_edit.setPlaceholderText("x,y,z  (hole direction, optional)")
        self.direction_edit.editingFinished.connect(self._apply)
        form.addRow("Direction:", self.direction_edit)

        self.sketch_label = QLabel()
        form.addRow("Sketch ID:", self.sketch_label)

        layout.addLayout(form)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply)
        layout.addWidget(self.apply_btn)
        layout.addStretch()

        self.current_feature: Optional[Union[ExtrudeFeature, RevolveFeature, HoleFeature]] = None
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
        self, feature: Optional[Union[ExtrudeFeature, RevolveFeature, HoleFeature]]
    ) -> None:
        self.current_feature = feature
        if feature is None:
            self.name_edit.clear()
            self.distance_edit.clear()
            self.offset_edit.clear()
            self.direction_edit.clear()
            self.sketch_label.clear()
            self.setEnabled(False)
            return
        self.setEnabled(True)
        self.name_edit.setText(feature.name)
        self.direction_edit.setEnabled(False)
        self.direction_edit.clear()
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
            self.offset_edit.clear()
            self.offset_edit.setEnabled(False)
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
                self.history.features[i] = self.current_feature.to_dict()
                self.history.validate()
                break
        self.properties_changed.emit()
