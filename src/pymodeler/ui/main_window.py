"""Minimal PyQt6 main window for PyModeler.

Provides menu, outliner, OpenGL viewport, and properties.
Supports adding primitives that are validated against the mesh schema.
"""

from __future__ import annotations

import sys
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QStatusBar,
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
)
from pymodeler.render import ViewportWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyModeler")
        self.resize(1200, 800)

        self.scene = Scene(name="Main Scene")
        self.history = CommandStack()
        self._object_counter = 0

        self._build_menu()
        self._build_ui()
        self._update_outliner()
        self.statusBar().showMessage("Ready – drag to orbit, Shift+drag to pan, wheel to zoom")

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        file_menu.addAction("New", self.new_scene)
        file_menu.addAction("Quit", self.close)

        edit_menu = menubar.addMenu("&Edit")
        self.undo_action = edit_menu.addAction("Undo", self.undo)
        self.undo_action.setShortcut("Ctrl+Z")
        self.redo_action = edit_menu.addAction("Redo", self.redo)
        self.redo_action.setShortcut("Ctrl+Shift+Z")
        edit_menu.addSeparator()
        delete_action = edit_menu.addAction("Delete Selected", self.delete_selected)
        delete_action.setShortcut("Delete")

        add_menu = menubar.addMenu("&Add")
        mesh_menu = add_menu.addMenu("Mesh")
        mesh_menu.addAction("Cube", self.add_cube)
        mesh_menu.addAction("Plane", self.add_plane)
        mesh_menu.addAction("Sphere", self.add_sphere)
        mesh_menu.addAction("Cylinder", self.add_cylinder)
        mesh_menu.addAction("Cone", self.add_cone)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Outliner
        self.outliner = QTreeWidget()
        self.outliner.setHeaderLabel("Outliner")
        self.outliner.itemSelectionChanged.connect(self._on_outliner_selection)
        splitter.addWidget(self.outliner)

        # Viewport (OpenGL)
        self.viewport = ViewportWidget()
        self.viewport.set_scene(self.scene)
        splitter.addWidget(self.viewport)

        # Properties
        self.properties = QTextEdit()
        self.properties.setReadOnly(True)
        self.properties.setPlaceholderText("Select an object to view properties")
        splitter.addWidget(self.properties)

        splitter.setSizes([250, 700, 250])
        layout.addWidget(splitter)

        self.setStatusBar(QStatusBar())

    def new_scene(self) -> None:
        self.scene = Scene(name="Main Scene")
        self.history.clear()
        self._object_counter = 0
        self.viewport.set_scene(self.scene)
        self._update_outliner()
        self.properties.clear()
        self.statusBar().showMessage("New scene")
        self._update_edit_actions()

    def undo(self) -> None:
        if self.history.undo():
            self.viewport.set_scene(self.scene)
            self._update_outliner()
            self._update_edit_actions()
            self.statusBar().showMessage("Undo")

    def redo(self) -> None:
        if self.history.redo():
            self.viewport.set_scene(self.scene)
            self._update_outliner()
            self._update_edit_actions()
            self.statusBar().showMessage("Redo")

    def delete_selected(self) -> None:
        selected = self.scene.selected_objects()
        if not selected:
            return
        # Delete in reverse order so indices stay valid if we used index-based, but name-based is fine
        for obj in reversed(selected):
            cmd = RemoveObjectCommand(self.scene, obj)
            self.history.push(cmd)
        self.viewport.set_scene(self.scene)
        self._update_outliner()
        self.properties.clear()
        self._update_edit_actions()
        self.statusBar().showMessage(f"Deleted {len(selected)} object(s)")

    def _update_edit_actions(self) -> None:
        self.undo_action.setEnabled(self.history.can_undo())
        self.redo_action.setEnabled(self.history.can_redo())

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

    def _add_primitive(self, base_name: str, factory) -> None:
        self._object_counter += 1
        name = f"{base_name}.{self._object_counter:03d}" if self._object_counter > 1 else base_name
        mesh = factory(name=name)
        obj = SceneObject(name=name, mesh=mesh)
        cmd = AddObjectCommand(self.scene, obj)
        self.history.push(cmd)
        self.scene.validate()
        # Select the newly added object
        self.scene.select(obj, clear=True)
        self.viewport.set_scene(self.scene)
        self._update_outliner()
        # Select the corresponding outliner item
        self._select_outliner_item(obj.name)
        self._update_edit_actions()
        self.statusBar().showMessage(f"Added {name}")

    def _update_outliner(self) -> None:
        self.outliner.clear()
        root = QTreeWidgetItem([self.scene.name])
        self.outliner.addTopLevelItem(root)
        for obj in self.scene.objects:
            item = QTreeWidgetItem([obj.name])
            root.addChild(item)
        self.outliner.expandAll()

    def _select_outliner_item(self, name: str) -> None:
        """Select the outliner item matching the given object name."""
        root = self.outliner.topLevelItem(0)
        if root is None:
            return
        for i in range(root.childCount()):
            child = root.child(i)
            if child.text(0) == name:
                self.outliner.setCurrentItem(child)
                return

    def _on_outliner_selection(self) -> None:
        items = self.outliner.selectedItems()
        # Sync to scene selection (object mode)
        self.scene.clear_selection()
        selected_obj = None
        if items:
            name = items[0].text(0)
            # Ignore the root scene item
            if name != self.scene.name:
                self.scene.select(name, clear=True)
                selected_obj = self.scene.get_object(name)

        # Refresh viewport so selection highlight updates
        self.viewport.set_scene(self.scene)

        if selected_obj is None:
            self.properties.clear()
            return

        mesh = selected_obj.mesh
        text = (
            f"Name: {selected_obj.name}\n"
            f"Vertices: {len(mesh.vertices)}\n"
            f"Faces: {len(mesh.faces)}\n"
            f"Location: {selected_obj.transform.location}\n"
            f"Rotation: {selected_obj.transform.rotation}\n"
            f"Scale: {selected_obj.transform.scale}\n"
            f"Visible: {selected_obj.visible}\n"
            f"Selected: yes\n"
        )
        self.properties.setPlainText(text)


def run_app() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
