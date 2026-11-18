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
    QFileDialog,
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
    FeatureHistory,
    ParameterStore,
    Sketch,
    create_rectangle_sketch,
    ExtrudeFeature,
    RevolveFeature,
    Part,
    generate_cut_list,
    cut_list_to_text,
    cut_list_to_grouped_text,
    cut_list_to_csv,
    generate_bom,
    bom_to_text,
    bom_to_csv,
    Assembly,
    Instance,
    Mate,
    Transform,
)
from pymodeler.render import ViewportWidget
from pymodeler.ui.feature_tree import FeatureTreeWidget, PropertyPanel
from pymodeler.ui.sketch_editor import SketchEditorWidget

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
        # Parametric Part as the primary working unit
        self.current_part = Part(name="Part 1")
        self.parts: list[Part] = [self.current_part]
        self.current_sketch: Optional[Sketch] = None
        self.current_assembly: Optional[Assembly] = None

        self.viewport = ViewportWidget()
        self.viewport.set_scene(self.scene)
        self.viewport.selection_changed.connect(self._sync_outliner_from_scene)
        # Transform commit is currently a no-op stub; full parametric transform later
        if hasattr(self.viewport, "transform_committed"):
            self.viewport.transform_committed.connect(self._on_transform_committed)

        self.outliner = QListWidget()
        self.outliner.itemSelectionChanged.connect(self._on_outliner_selection)

        # Parts list for multi-part switching
        self.part_list = QListWidget()
        self.part_list.itemSelectionChanged.connect(self._on_part_selection)
        self.part_label = QLabel(f"Timeline / Features — {self.current_part.name}")

        self.feature_tree = FeatureTreeWidget()
        self.feature_tree.set_history(self.current_part.feature_history)
        self.property_panel = PropertyPanel()
        self.property_panel.set_context(
            self.current_part.feature_history, self.current_part.parameters
        )
        self.feature_tree.feature_selected.connect(self.property_panel.show_feature)
        self.property_panel.properties_changed.connect(self.feature_tree.refresh)
        self.property_panel.properties_changed.connect(self._recompute_and_update_scene)
        self.feature_tree.rollback_changed.connect(self._recompute_and_update_scene)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Parts"))
        left_layout.addWidget(self.part_list)
        left_layout.addWidget(QLabel("Outliner"))
        left_layout.addWidget(self.outliner)
        left_layout.addWidget(self.part_label)
        left_layout.addWidget(self.feature_tree)
        left_layout.addWidget(self.property_panel)
        splitter.addWidget(left)
        splitter.addWidget(self.viewport)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)
        self._build_menus()
        self._refresh_part_list()
        self._refresh_outliner()

    def _build_menus(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        quit_act = QAction("Quit", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        part_menu = menubar.addMenu("&Part")
        new_part_act = QAction("New Part", self)
        new_part_act.triggered.connect(self._new_part)
        part_menu.addAction(new_part_act)

        sketch_menu = menubar.addMenu("&Sketch")
        new_sketch_act = QAction("New Sketch", self)
        new_sketch_act.triggered.connect(self._new_sketch)
        sketch_menu.addAction(new_sketch_act)
        edit_sketch_act = QAction("Edit Current Sketch", self)
        edit_sketch_act.triggered.connect(self._edit_sketch)
        sketch_menu.addAction(edit_sketch_act)
        rect_act = QAction("Add Rectangle Sketch", self)
        rect_act.triggered.connect(self._add_rectangle_sketch)
        sketch_menu.addAction(rect_act)
        extrude_act = QAction("Extrude Current Sketch", self)
        extrude_act.triggered.connect(self._extrude_current_sketch)
        sketch_menu.addAction(extrude_act)

        mfg_menu = menubar.addMenu("&Manufacturing")
        cutlist_act = QAction("Show Cut List", self)
        cutlist_act.triggered.connect(self._show_cut_list)
        mfg_menu.addAction(cutlist_act)
        grouped_act = QAction("Show Grouped Cut List", self)
        grouped_act.triggered.connect(self._show_grouped_cut_list)
        mfg_menu.addAction(grouped_act)
        export_cl_act = QAction("Export Cut List CSV...", self)
        export_cl_act.triggered.connect(self._export_cutlist_csv)
        mfg_menu.addAction(export_cl_act)
        mfg_menu.addSeparator()
        bom_act = QAction("Show BOM", self)
        bom_act.triggered.connect(self._show_bom)
        mfg_menu.addAction(bom_act)
        export_bom_act = QAction("Export BOM CSV...", self)
        export_bom_act.triggered.connect(self._export_bom_csv)
        mfg_menu.addAction(export_bom_act)

        asm_menu = menubar.addMenu("&Assembly")
        new_asm_act = QAction("New Assembly from Parts", self)
        new_asm_act.triggered.connect(self._new_assembly_from_parts)
        asm_menu.addAction(new_asm_act)
        add_mate_act = QAction("Add Rigid Mate...", self)
        add_mate_act.triggered.connect(self._add_rigid_mate)
        asm_menu.addAction(add_mate_act)
        solve_act = QAction("Solve Mates", self)
        solve_act.triggered.connect(self._solve_mates)
        asm_menu.addAction(solve_act)
        show_asm_act = QAction("Show Assembly Summary", self)
        show_asm_act.triggered.connect(self._show_assembly_summary)
        asm_menu.addAction(show_asm_act)

    def _on_transform_committed(self, *args) -> None:
        """Stub for viewport transform commit. Parametric transforms come later."""
        pass

    def _refresh_part_list(self) -> None:
        """Refresh the parts list and select the current part."""
        self.part_list.blockSignals(True)
        self.part_list.clear()
        for part in self.parts:
            self.part_list.addItem(part.name)
        # Select current
        for i, part in enumerate(self.parts):
            if part is self.current_part:
                self.part_list.item(i).setSelected(True)
                break
        self.part_list.blockSignals(False)
        self.part_label.setText(f"Timeline / Features — {self.current_part.name}")

    def _on_part_selection(self) -> None:
        """Switch the current part when selection changes."""
        selected = self.part_list.selectedItems()
        if not selected:
            return
        name = selected[0].text()
        for part in self.parts:
            if part.name == name:
                self._switch_to_part(part)
                break

    def _switch_to_part(self, part: Part) -> None:
        """Switch working part, update feature tree, properties, and viewport."""
        self.current_part = part
        self.feature_tree.set_history(part.feature_history)
        self.property_panel.set_context(part.feature_history, part.parameters)
        self.part_label.setText(f"Timeline / Features — {part.name}")
        # Clear current sketch on switch for safety (sketches belong to parts)
        self.current_sketch = None
        self._recompute_and_update_scene()

    def _new_part(self) -> None:
        """Create a new empty Part and switch to it."""
        n = len(self.parts) + 1
        new_part = Part(name=f"Part {n}")
        self.parts.append(new_part)
        self._refresh_part_list()
        self._switch_to_part(new_part)

    def _show_cut_list(self) -> None:
        """Generate and display a simple cut list for current parts."""
        try:
            cl = generate_cut_list(self.parts)
            text = cut_list_to_text(cl)
            QMessageBox.information(self, "Cut List", text or "No parts with geometry.")
        except Exception as e:
            QMessageBox.warning(self, "Cut List", f"Could not generate cut list:\n{e}")

    def _show_grouped_cut_list(self) -> None:
        """Generate and display a cut list grouped by material/thickness."""
        try:
            cl = generate_cut_list(self.parts)
            text = cut_list_to_grouped_text(cl)
            QMessageBox.information(self, "Grouped Cut List", text or "No parts with geometry.")
        except Exception as e:
            QMessageBox.warning(self, "Grouped Cut List", f"Could not generate grouped cut list:\n{e}")

    def _export_cutlist_csv(self) -> None:
        """Export the current cut list (with groups) to a CSV file."""
        try:
            cl = generate_cut_list(self.parts)
            csv_text = cut_list_to_csv(cl, include_groups=True)
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Cut List CSV", "cutlist.csv", "CSV Files (*.csv);;All Files (*)"
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(csv_text)
                QMessageBox.information(self, "Export", f"Cut list saved to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Cut List", f"Could not export cut list:\n{e}")

    def _show_bom(self) -> None:
        """Generate and display a BOM for current parts (or assembly if present)."""
        try:
            if self.current_assembly is not None:
                bom = generate_bom(assembly=self.current_assembly, parts_map={p.id: p for p in self.parts})
            else:
                bom = generate_bom(parts=self.parts)
            text = bom_to_text(bom)
            QMessageBox.information(self, "BOM", text or "No items.")
        except Exception as e:
            QMessageBox.warning(self, "BOM", f"Could not generate BOM:\n{e}")

    def _export_bom_csv(self) -> None:
        """Export the current BOM to a CSV file."""
        try:
            if self.current_assembly is not None:
                bom = generate_bom(assembly=self.current_assembly, parts_map={p.id: p for p in self.parts})
            else:
                bom = generate_bom(parts=self.parts)
            csv_text = bom_to_csv(bom)
            path, _ = QFileDialog.getSaveFileName(
                self, "Export BOM CSV", "bom.csv", "CSV Files (*.csv);;All Files (*)"
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(csv_text)
                QMessageBox.information(self, "Export", f"BOM saved to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export BOM", f"Could not export BOM:\n{e}")

    def _new_assembly_from_parts(self) -> None:
        """Create a new Assembly and add all current Parts as instances (first grounded)."""
        if not self.parts:
            QMessageBox.information(self, "Assembly", "No parts available.")
            return
        self.current_assembly = Assembly(name="Assembly 1")
        for i, part in enumerate(self.parts):
            grounded = (i == 0)
            self.current_assembly.add_instance(part, grounded=grounded)
        QMessageBox.information(
            self,
            "Assembly",
            f"Created assembly '{self.current_assembly.name}' with {len(self.current_assembly.instances)} instances.\n"
            "First instance is grounded. Use 'Add Rigid Mate...' then 'Solve Mates'.",
        )

    def _add_rigid_mate(self) -> None:
        """Dialog to add a rigid/fastened mate between two instances."""
        if self.current_assembly is None or len(self.current_assembly.instances) < 2:
            QMessageBox.information(self, "Add Mate", "Create an assembly with at least two instances first.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Rigid Mate")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        inst_names = [f"{inst.name} ({inst.id[-4:]})" for inst in self.current_assembly.instances]
        combo_a = QComboBox()
        combo_a.addItems(inst_names)
        combo_b = QComboBox()
        combo_b.addItems(inst_names)
        if len(inst_names) > 1:
            combo_b.setCurrentIndex(1)
        form.addRow("Instance A:", combo_a)
        form.addRow("Instance B:", combo_b)
        ox = QDoubleSpinBox()
        ox.setRange(-1000, 1000)
        ox.setValue(0.0)
        oy = QDoubleSpinBox()
        oy.setRange(-1000, 1000)
        oy.setValue(0.0)
        oz = QDoubleSpinBox()
        oz.setRange(-1000, 1000)
        oz.setValue(0.0)
        form.addRow("Offset X:", ox)
        form.addRow("Offset Y:", oy)
        form.addRow("Offset Z:", oz)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        idx_a = combo_a.currentIndex()
        idx_b = combo_b.currentIndex()
        if idx_a == idx_b:
            QMessageBox.warning(self, "Add Mate", "Select two different instances.")
            return
        inst_a = self.current_assembly.instances[idx_a]
        inst_b = self.current_assembly.instances[idx_b]
        offset = Transform(location=[ox.value(), oy.value(), oz.value()])
        try:
            self.current_assembly.add_mate(inst_a, inst_b, type="rigid", offset=offset)
            QMessageBox.information(self, "Add Mate", f"Added rigid mate between {inst_a.name} and {inst_b.name}.")
        except Exception as e:
            QMessageBox.warning(self, "Add Mate", f"Could not add mate:\n{e}")

    def _solve_mates(self) -> None:
        """Run the basic rigid mate solver and report results."""
        if self.current_assembly is None:
            QMessageBox.information(self, "Solve Mates", "No assembly present.")
            return
        try:
            self.current_assembly.solve_mates()
            # Summarize locations
            lines = ["Mates solved (location offsets applied). Current instance locations:"]
            for inst in self.current_assembly.instances:
                loc = inst.transform.location
                lines.append(f"  {inst.name}: ({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f}) {'[grounded]' if inst.grounded else ''}")
            QMessageBox.information(self, "Solve Mates", "\n".join(lines))
        except Exception as e:
            QMessageBox.warning(self, "Solve Mates", f"Solver failed:\n{e}")

    def _show_assembly_summary(self) -> None:
        """Display a text summary of the current assembly instances and mates."""
        if self.current_assembly is None:
            QMessageBox.information(self, "Assembly", "No assembly present. Use 'New Assembly from Parts'.")
            return
        lines = [f"Assembly: {self.current_assembly.name} (id={self.current_assembly.id})"]
        lines.append(f"Instances ({len(self.current_assembly.instances)}):")
        for inst in self.current_assembly.instances:
            loc = inst.transform.location
            lines.append(f"  - {inst.name} (part={inst.part_id}) loc=({loc[0]:.1f},{loc[1]:.1f},{loc[2]:.1f}) {'grounded' if inst.grounded else ''}")
        lines.append(f"Mates ({len(self.current_assembly.mates)}):")
        for mate in self.current_assembly.mates:
            lines.append(f"  - {mate.name} ({mate.type}): {mate.instance_a} → {mate.instance_b}")
        QMessageBox.information(self, "Assembly Summary", "\n".join(lines))

    def _new_sketch(self) -> None:
        self.current_sketch = Sketch(name="New Sketch")
        self._open_sketch_editor()

    def _add_rectangle_sketch(self) -> None:
        self.current_sketch = create_rectangle_sketch(name="Rectangle")
        self._open_sketch_editor()

    def _edit_sketch(self) -> None:
        if self.current_sketch is None:
            self.current_sketch = Sketch(name="Sketch")
        self._open_sketch_editor()

    def _open_sketch_editor(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Sketch Editor")
        dialog.resize(700, 500)
        layout = QVBoxLayout(dialog)
        editor = SketchEditorWidget()
        editor.set_sketch(self.current_sketch)
        layout.addWidget(editor)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

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

    def _extrude_current_sketch(self) -> None:
        if self.current_sketch is None:
            QMessageBox.information(self, "Extrude", "Create or select a sketch first.")
            return
        self.current_part.add_sketch(self.current_sketch)
        feat = ExtrudeFeature(sketch_id=self.current_sketch.id, distance=5.0, name="Extrude")
        self.current_part.feature_history.add_extrude(feat)
        self.feature_tree.refresh()
        self._recompute_and_update_scene()

    def _recompute_and_update_scene(self) -> None:
        """Regenerate the Part body and place it in the scene."""
        body = self.current_part.recompute()
        self.scene.objects.clear()
        self.scene.selected.clear()
        if body is not None:
            obj = SceneObject(name=self.current_part.name, mesh=body)
            self.scene.objects.append(obj)
        self._refresh_outliner()
        self.viewport.set_scene(self.scene)
        self.viewport.update()
        self.viewport.frame_all()

def run_app() -> int:
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
