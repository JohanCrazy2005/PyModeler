"""Main application window for PyModeler.

Provides the primary UI: viewport, feature tree, parts list, assembly/manufacturing
actions, and parametric-intent transform handling.
"""

from __future__ import annotations

from typing import Optional, List

from PyQt6.QtCore import Qt
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
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pymodeler.core import (
    Assembly,
    CommandStack,
    ExtrudeMeshCommand,
    Part,
    Scene,
    SceneObject,
    Transform,
    create_cube,
)
from pymodeler.core.cutlist import generate_cut_list, cut_list_to_text
from pymodeler.core.nesting import NestingJob, nesting_job_from_parts
from pymodeler.core.parametric_transform import (
    apply_rotation_to_part_sketch_planes,
    apply_scale_to_part_sketches,
    apply_translation_to_part_sketches,
)
from pymodeler.render import ViewportWidget
from pymodeler.ui.feature_tree import FeatureTreeWidget, PropertyPanel
from pymodeler.ui.nesting_preview import show_nesting_preview
from pymodeler.ui.toolpath_preview import show_toolpath_preview
from pymodeler.core.toolpath import ToolpathJob


class ExtrudeDialog(QDialog):
    """Simple dialog for extrude distance and direction."""

    def __init__(self, default_distance: float = 1.0, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Extrude")
        layout = QFormLayout(self)

        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.01, 1000.0)
        self.distance_spin.setValue(default_distance)
        self.distance_spin.setSingleStep(0.1)
        layout.addRow("Distance:", self.distance_spin)

        self.axis_combo = QComboBox()
        self.axis_combo.addItems(["Average Normal", "X Axis", "Y Axis", "Z Axis"])
        layout.addRow("Direction:", self.axis_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_distance(self) -> float:
        return float(self.distance_spin.value())

    def get_direction(self) -> Optional[List[float]]:
        text = self.axis_combo.currentText()
        if text == "X Axis":
            return [1.0, 0.0, 0.0]
        if text == "Y Axis":
            return [0.0, 1.0, 0.0]
        if text == "Z Axis":
            return [0.0, 0.0, 1.0]
        return None  # Average Normal


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PyModeler")
        self.resize(1200, 800)

        # Core data
        self.scene = Scene(name="Main")
        self.history = CommandStack()
        self.parts: List[Part] = []
        self.current_part: Optional[Part] = None
        self.current_assembly: Optional[Assembly] = None

        # Start with one part
        part1 = Part(name="Part 1")
        self.parts.append(part1)
        self.current_part = part1

        # Widgets
        self.viewport = ViewportWidget()
        self.viewport.set_scene(self.scene)
        self.viewport.selection_changed.connect(self._on_selection_changed)
        self.viewport.transform_committed.connect(self._on_transform_committed)

        self.feature_tree = FeatureTreeWidget()
        self.feature_tree.set_history(self.current_part.feature_history)
        self.feature_tree.rollback_changed.connect(self._on_rollback)

        self.property_panel = PropertyPanel()

        self.part_list = QListWidget()
        self.part_list.itemClicked.connect(self._on_part_list_clicked)
        self._refresh_part_list()

        # Layout
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Parts"))
        left_layout.addWidget(self.part_list)
        left_layout.addWidget(QLabel("Features"))
        left_layout.addWidget(self.feature_tree)
        left_layout.addWidget(self.property_panel)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(self.viewport)
        splitter.setStretchFactor(1, 3)
        self.setCentralWidget(splitter)

        self._build_menus()

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------

    def _build_menus(self) -> None:
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("New Part", self._new_part)
        file_menu.addAction("Quit", self.close)

        # Create
        create_menu = menubar.addMenu("&Create")
        create_menu.addAction("Cube", self.add_cube)

        # Assembly
        assembly_menu = menubar.addMenu("&Assembly")
        assembly_menu.addAction("New Assembly from Parts", self._new_assembly_from_parts)

        # Manufacturing
        mfg_menu = menubar.addMenu("&Manufacturing")
        mfg_menu.addAction("Cut List", self._show_cutlist)
        mfg_menu.addAction("BOM (stub)", self._show_bom_stub)
        mfg_menu.addSeparator()
        mfg_menu.addAction("Nesting Preview…", self._show_nesting_preview)
        mfg_menu.addAction("Toolpath Preview…", self._show_toolpath_preview)

        # View
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("Frame All", self.viewport.frame_all)
        view_menu.addAction("Frame Selected", self.viewport.frame_selected)
        view_menu.addAction("Toggle Ortho", self.viewport.toggle_orthographic)

    # ------------------------------------------------------------------
    # Part management
    # ------------------------------------------------------------------

    def _refresh_part_list(self) -> None:
        self.part_list.clear()
        for p in self.parts:
            self.part_list.addItem(p.name)
        if self.current_part is not None:
            names = [self.part_list.item(i).text() for i in range(self.part_list.count())]
            if self.current_part.name in names:
                self.part_list.setCurrentRow(names.index(self.current_part.name))

    def _new_part(self) -> None:
        idx = len(self.parts) + 1
        part = Part(name=f"Part {idx}")
        self.parts.append(part)
        self._switch_to_part(part)
        self._refresh_part_list()

    def _switch_to_part(self, part: Part) -> None:
        self.current_part = part
        self.feature_tree.set_history(part.feature_history)
        self._refresh_part_list()
        # Optional: clear scene objects that belong to other parts (simple for now)
        self.viewport.update()

    def _on_part_list_clicked(self, item) -> None:
        name = item.text()
        for p in self.parts:
            if p.name == name:
                self._switch_to_part(p)
                break

    def _new_assembly_from_parts(self) -> None:
        if len(self.parts) < 2:
            QMessageBox.information(self, "Assembly", "Need at least two parts.")
            return
        asm = Assembly(name="Assembly 1")
        for i, part in enumerate(self.parts):
            grounded = i == 0
            asm.add_instance(part, grounded=grounded)
        self.current_assembly = asm
        QMessageBox.information(
            self, "Assembly", f"Created assembly with {len(asm.instances)} instances."
        )

    # ------------------------------------------------------------------
    # Object creation / editing
    # ------------------------------------------------------------------

    def add_cube(self) -> None:
        mesh = create_cube()
        obj = SceneObject(name="Cube", mesh=mesh)
        self.scene.add_object(obj)
        self.viewport.set_scene(self.scene)
        self.viewport.update()

    def _on_selection_changed(self) -> None:
        # Property panel is feature-oriented; selection of scene objects is handled by viewport
        self.viewport.update()

    def _on_rollback(self) -> None:
        if self.current_part is not None:
            self.current_part.recompute()
        self.viewport.update()

    def _on_transform_committed(self, obj, start_transform, end_transform) -> None:
        """Apply parametric transform intent to current part sketches when possible."""
        if self.current_part is None:
            return
        mode = self.viewport.gizmo_mode or "translate"
        try:
            if mode == "translate":
                start_loc = start_transform.location
                end_loc = end_transform.location
                dx = end_loc[0] - start_loc[0]
                dy = end_loc[1] - start_loc[1]
                dz = end_loc[2] - start_loc[2]
                if abs(dx) + abs(dy) + abs(dz) < 1e-6:
                    return
                apply_translation_to_part_sketches(self.current_part, dx, dy, dz)
            elif mode == "scale":
                start_s = start_transform.scale
                end_s = end_transform.scale
                sx = end_s[0] / (start_s[0] if abs(start_s[0]) > 1e-8 else 1.0)
                sy = end_s[1] / (start_s[1] if abs(start_s[1]) > 1e-8 else 1.0)
                sz = end_s[2] / (start_s[2] if abs(start_s[2]) > 1e-8 else 1.0)
                if abs(sx - 1.0) + abs(sy - 1.0) + abs(sz - 1.0) < 1e-6:
                    return
                apply_scale_to_part_sketches(self.current_part, sx, sy, sz)
            elif mode == "rotate":
                start_r = start_transform.rotation
                end_r = end_transform.rotation
                dax = end_r[0] - start_r[0]
                day = end_r[1] - start_r[1]
                daz = end_r[2] - start_r[2]
                if abs(dax) + abs(day) + abs(daz) < 1e-6:
                    return
                apply_rotation_to_part_sketch_planes(self.current_part, dax, day, daz)
            else:
                return

            self.current_part.recompute()
            # Reset free transform on the scene object so it matches recomputed body
            obj.transform.location = [0.0, 0.0, 0.0]
            obj.transform.rotation = [0.0, 0.0, 0.0]
            obj.transform.scale = [1.0, 1.0, 1.0]
            self.viewport.update()
        except Exception:
            # Keep free transform if parametric update fails
            pass

    def _show_cutlist(self) -> None:
        """Show real cut-list text generated from current parts."""
        if not self.parts:
            QMessageBox.information(self, "Cut List", "No parts available.")
            return
        try:
            cl = generate_cut_list(self.parts, name="Current Parts")
            text = cut_list_to_text(cl)
            QMessageBox.information(self, "Cut List", text)
        except Exception as exc:
            QMessageBox.warning(self, "Cut List", f"Generation failed: {exc}")

    def _show_bom_stub(self) -> None:
        QMessageBox.information(self, "BOM", "BOM generation available via core API.")

    def _show_nesting_preview(self) -> None:
        """Build nesting job from current parts (with sample fallback) and show preview."""
        if not self.parts:
            QMessageBox.information(self, "Nesting", "No parts available.")
            return
        try:
            job = nesting_job_from_parts(self.parts, name="Nesting from Parts")
            if not job.parts:
                QMessageBox.information(self, "Nesting", "No nestable parts found.")
                return
            job.pack()
            show_nesting_preview(job, self)
        except Exception as exc:
            QMessageBox.warning(self, "Nesting", f"Could not prepare nesting: {exc}")


    def _show_toolpath_preview(self) -> None:
        """Create a sample rectangular toolpath from current part size (or default) and show preview."""
        # Prefer current part body extents if available; fall back to a sensible default
        width, height, depth = 80.0, 50.0, 5.0
        if self.current_part is not None and hasattr(self.current_part, "get_body"):
            try:
                body = self.current_part.get_body()
                if body and getattr(body, "vertices", None):
                    xs = [v[0] for v in body.vertices]
                    ys = [v[1] for v in body.vertices]
                    zs = [v[2] for v in body.vertices]
                    width = max(max(xs) - min(xs), 20.0)
                    height = max(max(ys) - min(ys), 20.0)
                    depth = max(max(zs) - min(zs), 2.0)
            except Exception:
                pass
        try:
            job = ToolpathJob(
                operation="pocket",
                width=width,
                height=height,
                depth=depth,
                tool_diameter=6.0,
                strategy="concentric",
                name="Sample Pocket",
            )
            job.generate()
            show_toolpath_preview(job, self)
        except Exception as exc:
            QMessageBox.warning(self, "Toolpath", f"Could not prepare toolpath: {exc}")

    def undo(self) -> None:
        self.history.undo()
        self.viewport.update()

    def redo(self) -> None:
        self.history.redo()
        self.viewport.update()


def run_app() -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
