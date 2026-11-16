"""Additional tests for feature tree rollback UI."""

import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.core import ExtrudeFeature, FeatureHistory, create_rectangle_sketch
from pymodeler.ui.feature_tree import FeatureTreeWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_feature_tree_shows_suppressed_and_sets_rollback(qapp):
    hist = FeatureHistory()
    sketch = create_rectangle_sketch()
    f1 = ExtrudeFeature(sketch_id=sketch.id, distance=1.0, name="First")
    f2 = ExtrudeFeature(sketch_id=sketch.id, distance=2.0, name="Second")
    hist.add_extrude(f1)
    hist.add_extrude(f2)

    tree = FeatureTreeWidget()
    tree.set_history(hist)
    assert tree.count() == 2
    assert "First" in tree.item(0).text()
    assert "[suppressed]" not in tree.item(0).text()
    assert "[suppressed]" not in tree.item(1).text()

    # Set rollback after first feature
    tree._set_rollback(1)
    assert hist.rollback_marker == 1
    assert "[suppressed]" in tree.item(1).text()
    assert "[suppressed]" not in tree.item(0).text()

    # Roll to end
    tree._set_rollback(None)
    assert hist.rollback_marker is None
    assert "[suppressed]" not in tree.item(1).text()

    tree.close()
