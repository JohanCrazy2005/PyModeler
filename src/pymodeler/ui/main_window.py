"""Main application window for PyModeler.

Integrates the viewport, outliner, scene, undo/redo history, and menus.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
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
)
from pymodeler.render import ViewportWidget


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

        # View
        view_menu = menubar.addMenu("&View")
        wire_act = QAction("Toggle Wireframe", self)
        wire_act.setShortcut(QKeySequence("Z"))
        wire_act.triggered.connect(self.viewport.toggle_wireframe)
        view_menu.addAction(wire_act)

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
            "  Z: Toggle Wireframe\n\n"
            "Gizmo\n"
            "  G: Translate\n"
            "  R: Rotate\n"
            "  S: Scale\n\n"
            "Edit\n"
            "  Ctrl+Z: Undo\n"
            "  Ctrl+Shift+Z: Redo\n"
            "  Delete: Delete selected\n"
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
