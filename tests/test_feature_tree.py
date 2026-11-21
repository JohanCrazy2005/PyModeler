"""Tests for the feature tree / timeline UI stub."""

import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.core import (
    ExtrudeFeature,
    FeatureHistory,
    HoleFeature,
    ParameterStore,
    create_rectangle_sketch,
)
from pymodeler.ui.feature_tree import FeatureTreeWidget, PropertyPanel


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_feature_tree_displays_features(qapp):
    hist = FeatureHistory()
    sketch = create_rectangle_sketch(width=10, height=5)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=2.5, name="Box")
    hist.add_extrude(feat)

    tree = FeatureTreeWidget()
    tree.set_history(hist)
    assert tree.count() == 1
    assert "Box" in tree.item(0).text()
    tree.close()


def test_property_panel_shows_and_edits(qapp):
    hist = FeatureHistory()
    params = ParameterStore()
    sketch = create_rectangle_sketch()
    feat = ExtrudeFeature(sketch_id=sketch.id, distance="height", name="ParamBox")
    hist.add_extrude(feat)

    panel = PropertyPanel()
    panel.set_context(hist, params)
    panel.show_feature(feat)
    assert panel.name_edit.text() == "ParamBox"
    assert panel.distance_edit.text() == "height"
    assert panel.sketch_label.text() == sketch.id

    # Edit
    panel.name_edit.setText("Renamed")
    panel.distance_edit.setText("10")
    panel._apply()
    assert hist.features[0]["name"] == "Renamed"
    assert hist.features[0]["distance"] == 10.0
    panel.close()


def test_property_panel_hole_direction(qapp):
    hist = FeatureHistory()
    params = ParameterStore()
    hole = HoleFeature(
        diameter=8.0,
        depth=20.0,
        name="MountHole",
        direction=[0.0, 0.0, -1.0],
    )
    hist.add_hole(hole)

    panel = PropertyPanel()
    panel.set_context(hist, params)
    panel.show_feature(hole)
    assert panel.name_edit.text() == "MountHole"
    assert panel.distance_edit.text() == "8.0"
    assert panel.offset_edit.text() == "20.0"
    assert panel.direction_edit.text() == "0.0,0.0,-1.0"
    assert panel.direction_edit.isEnabled()

    # Edit direction and diameter
    panel.distance_edit.setText("10")
    panel.direction_edit.setText("1,0,0")
    panel._apply()
    updated = hist.features[0]
    assert updated["diameter"] == 10.0
    assert updated["direction"] == [1.0, 0.0, 0.0]
    panel.close()
