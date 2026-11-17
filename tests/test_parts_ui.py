"""Tests for multi-part switching UI in MainWindow."""

import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.core import Part
from pymodeler.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_initial_part_list(qapp):
    window = MainWindow()
    assert len(window.parts) == 1
    assert window.parts[0].name == "Part 1"
    assert window.current_part is window.parts[0]
    assert window.part_list.count() == 1
    window.close()


def test_new_part_and_switch(qapp):
    window = MainWindow()
    window._new_part()
    assert len(window.parts) == 2
    assert window.current_part.name == "Part 2"
    assert window.part_list.count() == 2
    # Switch back
    window._switch_to_part(window.parts[0])
    assert window.current_part.name == "Part 1"
    assert window.feature_tree.history is window.parts[0].feature_history
    window.close()
