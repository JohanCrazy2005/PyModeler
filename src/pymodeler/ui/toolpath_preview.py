"""Simple UI preview for rectangular toolpath / G-code.

Shows generated G-code text and a 2D path plot (parsed from G00/G01/G03 lines)
using PyQt6 QPainter. Cross-platform, no extra dependencies.
"""

from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pymodeler.core.toolpath import ToolpathJob, parse_gcode_paths


class ToolpathPreviewWidget(QWidget):
    """Paints the 2D tool center path extracted from G-code.

    Scales the bounding box of all points to fit the widget with margin.
    Draws path segments in blue, with start marker.
    """

    def __init__(self, job: Optional[ToolpathJob] = None, parent=None) -> None:
        super().__init__(parent)
        self.job = job
        self.setMinimumSize(300, 250)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(245, 245, 245))
        self.setPalette(pal)

    def set_job(self, job: ToolpathJob) -> None:
        self.job = job
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.job is None or not self.job.gcode:
            painter.setPen(QColor(120, 120, 120))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No toolpath generated")
            return

        segments = parse_gcode_paths(self.job.gcode)
        if not segments:
            painter.setPen(QColor(120, 120, 120))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No path points")
            return

        # Bounding box
        all_pts = [p for seg in segments for p in seg]
        if not all_pts:
            return
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1e-3)
        span_y = max(max_y - min_y, 1e-3)

        margin = 24
        avail_w = self.width() - 2 * margin
        avail_h = self.height() - 2 * margin
        scale = min(avail_w / span_x, avail_h / span_y)
        # Center
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        origin_x = self.width() / 2.0 - cx * scale
        origin_y = self.height() / 2.0 + cy * scale  # Y up in model, down in screen? flip for typical CAD

        def to_screen(px: float, py: float) -> QPointF:
            sx = origin_x + px * scale
            sy = origin_y - py * scale  # flip Y so positive Y is up
            return QPointF(sx, sy)

        # Feature outline (nominal rectangle)
        w = self.job.width
        h = self.job.height
        ox = self.job.origin_x
        oy = self.job.origin_y
        outline = [
            to_screen(ox, oy),
            to_screen(ox + w, oy),
            to_screen(ox + w, oy + h),
            to_screen(ox, oy + h),
        ]
        painter.setPen(QPen(QColor(180, 180, 180), 1, Qt.PenStyle.DashLine))
        for i in range(4):
            painter.drawLine(outline[i], outline[(i + 1) % 4])

        # Paths
        painter.setPen(QPen(QColor(30, 100, 220), 2))
        for seg in segments:
            if len(seg) < 2:
                continue
            for i in range(len(seg) - 1):
                p1 = to_screen(*seg[i])
                p2 = to_screen(*seg[i + 1])
                painter.drawLine(p1, p2)
            # Start marker
            start = to_screen(*seg[0])
            painter.setBrush(QColor(30, 100, 220))
            painter.drawEllipse(start, 4, 4)

        # Info
        painter.setPen(QColor(60, 60, 60))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        info = f"{self.job.operation} {self.job.strategy}  length≈{self.job.estimated_length:.1f}"
        painter.drawText(QRectF(8, 4, self.width() - 16, 16), Qt.AlignmentFlag.AlignLeft, info)


class ToolpathPreviewDialog(QDialog):
    """Modal dialog showing G-code text + 2D path plot for a ToolpathJob."""

    def __init__(self, job: ToolpathJob, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Toolpath Preview – {job.name}")
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        summary = QLabel(
            f"{job.operation} {job.strategy}  "
            f"{job.width}×{job.height}×{job.depth}  "
            f"tool {job.tool_diameter}  "
            f"length≈{job.estimated_length:.1f}"
        )
        summary.setWordWrap(True)
        summary.setStyleSheet("font-family: monospace; padding: 4px;")
        layout.addWidget(summary)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(job.gcode or "(not generated)")
        text.setStyleSheet("font-family: monospace; font-size: 10pt;")
        splitter.addWidget(text)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        preview = ToolpathPreviewWidget(job)
        scroll.setWidget(preview)
        splitter.addWidget(scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


def show_toolpath_preview(job: ToolpathJob, parent=None) -> None:
    """Convenience launcher. Generates G-code if missing."""
    if not job.gcode:
        try:
            job.generate()
        except Exception:
            pass
    dlg = ToolpathPreviewDialog(job, parent)
    dlg.exec()
