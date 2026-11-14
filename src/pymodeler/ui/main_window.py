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


class ExtrudeDialog(QDialog):
    """Simple modal dialog for Extrude distance and axis locking.

    Axis options:
    - Average Normal: use the computed average face normal (or per-face if requested by caller)
    - X / Y / Z Axis: lock to the corresponding world axis
    """

    def __init__(self, parent: Optional[QWidget] = None, default_distance: float = 1.0) -> None:
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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_distance(self) -> float:
        return float(self.distance_spin.value())

    def get_direction(self) -> Optional[list[float]]:
        """Return locked direction or None for average normal."""
        text = self.axis_combo.currentText()
        if text == "X Axis":
            return [1.0, 0.0, 0.0]
        if text == "Y Axis":
            return [0.0, 1.0, 0.0]
        if text == "Z Axis":
            return [0.0, 0.0, 1.0]
        return None  # Average Normal


class InsetDialog(QDialog):
    """Simple modal dialog for Inset thickness and optional depth.

    Thickness is a fraction [0, 1] toward the face centroid.
    """

    def __init__(self, parent: Optional[QWidget] = None, default_thickness: float = 0.2, default_depth: float = 0.0) -> None:
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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_thickness(self) -> float:
        return float(self.thickness_spin.value())

    def get_depth(self) -> float:
        return float(self.depth_spin.value())


class MainWindow(QMainWindow):
    """Primary application window."""

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

        # Layout
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

    # ------------------------------------------------------------------
    # Menus & actions
    # ------------------------------------------------------------------

    def _build_menus(self) -> None:
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("&File")
        quit_act = QAction("Quit", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        # Add
        add_menu = menubar.addMenu("&Add")
        for name, method in [
            ("Cube", self.add_cube),
            ("Plane", self.add_plane),
            ("Sphere", self.add_sphere),
            ("Cylinder", self.add_cylinder),
            ("Cone", self.add_cone),
        ]:
            act = QAction(name, self)
            act.triggered.connect(method)
            add_menu.addAction(act)

        # Edit
        edit_menu = menubar.addMenu("&Edit")
        undo_act = QAction("Undo", self)
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        undo_act.triggered.connect(self.undo)
        edit_menu.addAction(undo_act)

        redo_act = QAction("Redo", self)
        redo_act.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        redo_act.triggered.connect(self.redo)
        edit_menu.addAction(redo_act)

        edit_menu.addSeparator()
        delete_act = QAction("Delete Selected", self)
        delete_act.setShortcut(QKeySequence.StandardKey.Delete)
        delete_act.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_act)

        # Mesh
        mesh_menu = menubar.addMenu("&Mesh")
        extrude_act = QAction("Extrude Region", self)
        extrude_act.setShortcut(QKeySequence("E"))
        extrude_act.triggered.connect(self.extrude_selected)
        mesh_menu.addAction(extrude_act)

        extrude_ind_act = QAction("Extrude Individual", self)
        extrude_ind_act.setShortcut(QKeySequence("Shift+E"))
        extrude_ind_act.triggered.connect(self.extrude_individual)
        mesh_menu.addAction(extrude_ind_act)

        inset_act = QAction("Inset Faces", self)
        inset_act.setShortcut(QKeySequence("I"))
        inset_act.triggered.connect(self.inset_selected)
        mesh_menu.addAction(inset_act)

        # View
        view_menu = menubar.addMenu("&View")
        wire_act = QAction("Toggle Wireframe", self)
        wire_act.setShortcut(QKeySequence("Z"))
        wire_act.triggered.connect(self.viewport.toggle_wireframe)
        view_menu.addAction(wire_act)

        normals_act = QAction("Toggle Normals Overlay", self)
        normals_act.setShortcut(QKeySequence("N"))
        normals_act.triggered.connect(self.viewport.toggle_normals)
        view_menu.addAction(normals_act)

        edges_act = QAction("Toggle Edge Overlay", self)
        edges_act.setShortcut(QKeySequence("Ctrl+E"))
        edges_act.triggered.connect(self.viewport.toggle_edges)
        view_menu.addAction(edges_act)

        frame_all_act = QAction("Frame All", self)
        frame_all_act.setShortcut(QKeySequence("Home"))
        frame_all_act.triggered.connect(self.viewport.frame_all)
        view_menu.addAction(frame_all_act)

        frame_sel_act = QAction("Frame Selected", self)
        frame_sel_act.setShortcut(QKeySequence("F"))
        frame_sel_act.triggered.connect(self.viewport.frame_selected)
        view_menu.addAction(frame_sel_act)

        # Gizmo modes
        gizmo_menu = menubar.addMenu("&Gizmo")
        for mode, key in [("Translate", "G"), ("Rotate", "R"), ("Scale", "S")]:
            act = QAction(mode, self)
            act.setShortcut(QKeySequence(key))
            act.triggered.connect(lambda checked=False, m=mode.lower(): self._set_gizmo_mode(m))
            gizmo_menu.addAction(act)

        # Help
        help_menu = menubar.addMenu("&Help")
        shortcuts_act = QAction("Keyboard Shortcuts", self)
        shortcuts_act.triggered.connect(self.show_keyboard_shortcuts)
        help_menu.addAction(shortcuts_act)

        about_act = QAction("About PyModeler", self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)

    def _set_gizmo_mode(self, mode: str) -> None:
        self.viewport.gizmo_mode = mode
        self.viewport.update()

    def show_keyboard_shortcuts(self) -> None:
        text = (
            "Navigation\n"
            "  Drag: Orbit\n"
            "  Shift+Drag: Pan\n"
            "  Wheel: Zoom\n"
            "  Home: Frame All\n"
            "  F: Frame Selected\n\n"
            "View\n"
            "  Z: Toggle Wireframe\n"
            "  N: Toggle Normals Overlay\n"
            "  Ctrl+E: Toggle Edge Overlay\n\n"
            "Gizmo\n"
            "  G: Translate\n"
            "  R: Rotate\n"
            "  S: Scale\n\n"
            "Edit\n"
            "  Ctrl+Z: Undo\n"
            "  Ctrl+Shift+Z: Redo\n"
            "  Delete: Delete selected\n"
            "  E: Extrude Region (opens distance/axis dialog)\n"
            "  Shift+E: Extrude Individual (opens distance/axis dialog)\n"
            "  I: Inset Faces (opens thickness/depth dialog)\n"
        )
        QMessageBox.information(self, "Keyboard Shortcuts", text)

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About PyModeler",
            "PyModeler\n\nCross-platform 3D modeling software built with PyQt6.\n"
            "Incremental open-source development toward professional modeling capabilities.",
        )

    # ------------------------------------------------------------------
    # Object creation (via history)
    # ------------------------------------------------------------------

    def _add_primitive(self, name: str, mesh_factory) -> None:
        mesh = mesh_factory()
        obj = SceneObject(name=name, mesh=mesh)
        cmd = AddObjectCommand(self.scene, obj)
        self.history.push(cmd)
        self.scene.select(obj, clear=True)
        self._refresh_outliner()
        self.viewport.update()

    def add_cube(self) -> None:
        self._add_primitive("Cube", create_cube)

    def add_plane(self) -> None:
        self._add_primitive("Plane", create_plane)

    def add_sphere(self) -> None:
        self._add_primitive("Sphere", create_sphere)

    def add_cylinder(self) -> None:
        self._add_primitive("Cylinder", create_cylinder)

    def add_cone(self) -> None:
        self._add_primitive("Cone", create_cone)

    def delete_selected(self) -> None:
        selected = self.scene.selected_objects()
        if not selected:
            return
        # Delete in reverse order so indices stay valid
        for obj in reversed(selected):
            cmd = RemoveObjectCommand(self.scene, obj)
            self.history.push(cmd)
        self._refresh_outliner()
        self.viewport.update()

    def extrude_selected(self) -> None:
        """Extrude all faces of every selected object as a region.

        Opens a dialog for distance and axis locking. Fully undoable.
        """
        self._do_extrude(individual=False, use_per_face_normals=False)

    def extrude_individual(self) -> None:
        """Extrude each face of every selected object independently.

        Opens a dialog for distance and axis locking. Fully undoable.
        """
        self._do_extrude(individual=True, use_per_face_normals=True)

    def _do_extrude(self, individual: bool, use_per_face_normals: bool) -> None:
        selected = self.scene.selected_objects()
        if not selected:
            return

        # Show distance / axis dialog
        dialog = ExtrudeDialog(self, default_distance=1.0)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        distance = dialog.get_distance()
        locked_direction = dialog.get_direction()

        import numpy as np

        for obj in selected:
            mesh = obj.mesh
            if not mesh.faces:
                continue

            if locked_direction is not None:
                direction = locked_direction
                # When axis-locked we ignore per-face normals for consistency
                effective_per_face = False
            else:
                # Compute average face normal for a sensible default direction
                normals = []
                for i in range(len(mesh.faces)):
                    n = mesh.compute_face_normal(i)
                    normals.append(n)
                if normals:
                    avg = np.mean(normals, axis=0)
                    length = np.linalg.norm(avg)
                    direction = (avg / length).tolist() if length > 1e-8 else [0.0, 0.0, 1.0]
                else:
                    direction = [0.0, 0.0, 1.0]
                effective_per_face = use_per_face_normals

            cmd = ExtrudeMeshCommand(
                obj,
                face_indices=None,  # all faces
                direction=direction,
                distance=distance,
                individual=individual,
                use_per_face_normals=effective_per_face,
            )
            self.history.push(cmd)

        self.viewport.update()

    def inset_selected(self) -> None:
        """Inset all faces of every selected object (individual mode).

        Opens a dialog for thickness fraction and optional depth. Fully undoable.
        """
        selected = self.scene.selected_objects()
        if not selected:
            return

        dialog = InsetDialog(self, default_thickness=0.2, default_depth=0.0)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        thickness = dialog.get_thickness()
        depth = dialog.get_depth()

        for obj in selected:
            mesh = obj.mesh
            if not mesh.faces:
                continue
            cmd = InsetMeshCommand(
                obj,
                face_indices=None,  # all faces
                thickness=thickness,
                depth=depth,
                individual=True,
            )
            self.history.push(cmd)

        self.viewport.update()

    def undo(self) -> None:
        self.history.undo()
        self._refresh_outliner()
        self.viewport.update()

    def redo(self) -> None:
        self.history.redo()
        self._refresh_outliner()
        self.viewport.update()

    def _on_transform_committed(self, obj, old_t, new_t) -> None:
        # The live preview already applied new_t; record the command for undo
        cmd = SetTransformCommand(obj, new_t)
        # execute() will re-apply the same transform (idempotent)
        self.history.push(cmd)
        self.viewport.update()

    # ------------------------------------------------------------------
    # Outliner sync
    # ------------------------------------------------------------------

    def _refresh_outliner(self) -> None:
        self.outliner.blockSignals(True)
        self.outliner.clear()
        for obj in self.scene.objects:
            self.outliner.addItem(obj.name)
        # Restore selection
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
    """Launch the application. Returns exit code."""
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
