"""Tests for nesting preview UI (widget construction + paint path)."""

import pytest
from PyQt6.QtWidgets import QApplication

from pymodeler.core.nesting import NestingJob
from pymodeler.ui.nesting_preview import NestingPreviewWidget, NestingPreviewDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_nesting_preview_widget_empty(qapp):
    w = NestingPreviewWidget()
    assert w.job is None
    w.show()
    w.repaint()
    w.close()


def test_nesting_preview_widget_with_job(qapp):
    job = NestingJob(sheet_width=1000, sheet_height=500, kerf=2.0, name="Test")
    job.add_part(width=200, height=100, quantity=3, name="A")
    job.add_part(width=150, height=80, quantity=2, name="B")
    job.pack()
    assert job.sheets_used >= 1
    assert len(job.layouts) >= 1

    w = NestingPreviewWidget(job)
    assert w.job is job
    w.resize(500, 400)
    w.show()
    w.repaint()  # exercises paintEvent
    w.close()


def test_nesting_preview_dialog(qapp):
    job = NestingJob(sheet_width=800, sheet_height=600)
    job.add_part(width=100, height=100, quantity=1, name="Box")
    job.pack()
    dlg = NestingPreviewDialog(job)
    assert dlg.windowTitle().startswith("Nesting Preview")
    dlg.show()
    dlg.close()
