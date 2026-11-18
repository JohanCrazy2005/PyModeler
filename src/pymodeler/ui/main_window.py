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

# ... truncated for this example; full content would be here in real call
