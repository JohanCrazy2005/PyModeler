"""Tests for multi-part switching UI in MainWindow."""

import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.core import Part, Transform
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


def test_assembly_and_mfg_menus(qapp):
    window = MainWindow()
    # Manufacturing and Assembly menus exist
    assert window.current_assembly is None
    # Create assembly
    window._new_part()  # two parts
    window._new_assembly_from_parts()
    assert window.current_assembly is not None
    assert len(window.current_assembly.instances) == 2
    assert window.current_assembly.instances[0].grounded
    # Add a mate programmatically to avoid dialog
    inst_a = window.current_assembly.instances[0]
    inst_b = window.current_assembly.instances[1]
    window.current_assembly.add_mate(inst_a, inst_b, type="rigid", offset=Transform(location=[10.0, 0, 0]))
    window.current_assembly.solve_mates()
    assert window.current_assembly.instances[1].transform.location[0] == 10.0
    window.close()
