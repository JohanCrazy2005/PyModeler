"""Tests for toolpath preview UI (widget construction + paint path + dialog).

Headless environments may lack libEGL; UI widget tests are skipped if Qt cannot initialize.
The pure parser test always runs.
"""

import pytest

from pymodeler.core.toolpath import ToolpathJob


def test_parse_gcode_paths_basic():
    from pymodeler.core.toolpath import parse_gcode_paths

    gcode = """
G00 X0 Y0
G01 X10 Y0
G01 X10 Y10
G00 Z5
G01 X0 Y10
"""
    segs = parse_gcode_paths(gcode)
    assert len(segs) >= 1
    assert any(len(s) >= 2 for s in segs)


def _try_qt():
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        return app
    except Exception as exc:
        pytest.skip(f"Qt display unavailable: {exc}")


def test_toolpath_preview_widget_empty():
    app = _try_qt()
    from pymodeler.ui.toolpath_preview import ToolpathPreviewWidget

    w = ToolpathPreviewWidget()
    assert w.job is None
    w.show()
    w.repaint()
    w.close()


def test_toolpath_preview_widget_with_job():
    app = _try_qt()
    from pymodeler.ui.toolpath_preview import ToolpathPreviewWidget

    job = ToolpathJob(
        operation="pocket",
        width=40,
        height=25,
        depth=3,
        tool_diameter=4,
        strategy="concentric",
        name="PreviewTest",
    )
    job.generate()
    assert job.gcode

    w = ToolpathPreviewWidget(job)
    assert w.job is job
    w.resize(400, 300)
    w.show()
    w.repaint()
    w.close()


def test_toolpath_preview_dialog():
    app = _try_qt()
    from pymodeler.ui.toolpath_preview import ToolpathPreviewDialog

    job = ToolpathJob(
        operation="contour",
        width=30,
        height=20,
        depth=2,
        tool_diameter=3,
        name="DlgTest",
    )
    job.generate()
    dlg = ToolpathPreviewDialog(job)
    assert dlg.windowTitle().startswith("Toolpath Preview")
    dlg.show()
    dlg.close()
