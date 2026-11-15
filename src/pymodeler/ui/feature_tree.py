"""Feature tree / timeline UI stub for PyModeler.

Displays FeatureHistory items and a simple property panel for the selected feature.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pymodeler.core import ExtrudeFeature, FeatureHistory, ParameterStore


class FeatureTreeWidget(QListWidget):
    """Simple list showing features from a FeatureHistory."""

    feature_selected = pyqtSignal(object)  # ExtrudeFeature or None

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.history: Optional[FeatureHistory] = None
        self.itemSelectionChanged.connect(self._on_selection)

    def set_history(self, history: FeatureHistory) -> None:
        self.history = history
        self.refresh()

    def refresh(self) -> None:
        self.blockSignals(True)
        self.clear()
        if self.history is not None:
            for feat in self.history.get_extrude_features():
                item = QListWidgetItem(f"{feat.name} ({feat.type})")
                item.setData(Qt.ItemDataRole.UserRole, feat)
                self.addItem(item)
        self.blockSignals(False)

    def _on_selection(self) -> None:
        items = self.selectedItems()
        if items:
            feat = items[0].data(Qt.ItemDataRole.UserRole)
            self.feature_selected.emit(feat)
        else:
            self.feature_selected.emit(None)


class PropertyPanel(QWidget):
    """Simple property editor for an ExtrudeFeature."""

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
        form.addRow("Distance:", self.distance_edit)

        self.sketch_label = QLabel()
        form.addRow("Sketch ID:", self.sketch_label)

        layout.addLayout(form)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply)
        layout.addWidget(self.apply_btn)
        layout.addStretch()

        self.current_feature: Optional[ExtrudeFeature] = None
        self.history: Optional[FeatureHistory] = None
        self.parameters: Optional[ParameterStore] = None

    def set_context(
        self,
        history: Optional[FeatureHistory],
        parameters: Optional[ParameterStore],
    ) -> None:
        self.history = history
        self.parameters = parameters

    def show_feature(self, feature: Optional[ExtrudeFeature]) -> None:
        self.current_feature = feature
        if feature is None:
            self.name_edit.clear()
            self.distance_edit.clear()
            self.sketch_label.clear()
            self.setEnabled(False)
            return
        self.setEnabled(True)
        self.name_edit.setText(feature.name)
        dist = feature.distance
        self.distance_edit.setText(str(dist) if not isinstance(dist, str) else dist)
        self.sketch_label.setText(feature.sketch_id)

    def _apply(self) -> None:
        if self.current_feature is None or self.history is None:
            return
        name = self.name_edit.text().strip() or "Extrude"
        dist_text = self.distance_edit.text().strip()
        # Try to keep as number if possible, else string (parameter)
        try:
            distance: float | str = float(dist_text)
        except ValueError:
            distance = dist_text or "0"

        # Update the feature in the history list
        for i, fdict in enumerate(self.history.features):
            if fdict.get("id") == self.current_feature.id:
                self.current_feature.name = name
                self.current_feature.distance = distance
                self.history.features[i] = self.current_feature.to_dict()
                self.history.validate()
                break
        self.properties_changed.emit()
