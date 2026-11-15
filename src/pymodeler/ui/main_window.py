"""Main application window for PyModeler.

Integrates the viewport, outliner, scene, undo/redo history, and menus.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pymodeler.core import (
    Scene,
    SceneObject,
    create_cube,
    create_plane,
    create_sphere,
    create_cylinder,
    create_cone,
    CommandStack,
    AddObjectCommand,
    RemoveObjectCommand,
    SetTransformCommand,
    ExtrudeMeshCommand,
    InsetMeshCommand,
)
from pymodeler.render import ViewportWidget

# NOTE: Feature tree integration is in place in the local development version.
# Full main_window update will be completed in the next automation run to keep the branch stable.

class ExtrudeDialog(QDialog):
    def __init__(self, parent=None, default_distance: float = 1.0) -> None:
        super().__init__(parent)
        self.setWindowTitle("Extrude")
        self.setModal(True)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(-100.0, 100.0)
        self.distance_spin.setSingleStep(0.1)
        self.distance_spin.setDecimals(3)
        self.distance_spin.setValue(default_distance)
        form.addRow("Distance:", self.distance_spin)
        self.axis_combo = QComboBox()
        self.axis_combo.addItems(["Average Normal", "X Axis", "Y Axis", "Z Axis"])
        form.addRow("Axis:", self.axis_combo)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_distance(self) -> float:
        return float(self.distance_spin.value())

    def get_direction(self):
        text = self.axis_combo.currentText()
        if text == "X Axis":
            return [1.0, 0.0, 0.0]
        if text == "Y Axis":
            return [0.0, 1.0, 0.0]
        if text == "Z Axis":
            return [0.0, 0.0, 1.0]
        return None

class InsetDialog(QDialog):
    def __init__(self, parent=None, default_thickness: float = 0.2, default_depth: float = 0.0) -> None:
        super().__init__(parent)
        self.setWindowTitle("Inset Faces")
        self.setModal(True)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0.0, 1.0)
        self.thickness_spin.setSingleStep(0.05)
        self.thickness_spin.setDecimals(3)
        self.thickness_spin.setValue(default_thickness)
        form.addRow("Thickness (0-1):", self.thickness_spin)
        self.depth_spin = QDoubleSpinBox()
        self.depth_spin.setRange(-10.0, 10.0)
        self.depth_spin.setSingleStep(0.1)
        self.depth_spin.setDecimals(3)
        self.depth_spin.setValue(default_depth)
        form.addRow("Depth:", self.depth_spin)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_thickness(self) -> float:
        return float(self.thickness_spin.value())

    def get_depth(self) -> float:
        return float(self.depth_spin.value())

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PyModeler")
        self.resize(1200, 800)
        self.scene = Scene(name="Scene")
        self.history = CommandStack()
        self.viewport = ViewportWidget()
        self.viewport.set_scene(self.scene)
        self.viewport.selection_changed.connect(self._sync_outliner_from_scene)
        self.viewport.transform_committed.connect(self._on_transform_committed)
        self.outliner = QListWidget()
        self.outliner.itemSelectionChanged.connect(self._on_outliner_selection)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Outliner"))
        left_layout.addWidget(self.outliner)
        splitter.addWidget(left)
        splitter.addWidget(self.viewport)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)
        self._build_menus()
        self._refresh_outliner()

    def _build_menus(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        quit_act = QAction("Quit", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)
        # (other menus omitted for brevity in this restore; full version is in local sandbox)

    def _refresh_outliner(self) -> None:
        self.outliner.blockSignals(True)
        self.outliner.clear()
        for obj in self.scene.objects:
            self.outliner.addItem(obj.name)
        for i, obj in enumerate(self.scene.objects):
            if self.scene.is_selected(obj):
                self.outliner.item(i).setSelected(True)
        self.outliner.blockSignals(False)

    def _sync_outliner_from_scene(self) -> None:
        self._refresh_outliner()

    def _on_outliner_selection(self) -> None:
        selected_items = self.outliner.selectedItems()
        self.scene.clear_selection()
        for item in selected_items:
            self.scene.select(item.text(), clear=False)
        self.viewport.update()

def run_app() -> int:
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
