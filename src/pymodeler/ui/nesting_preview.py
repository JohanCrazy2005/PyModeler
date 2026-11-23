"""Simple UI preview for rectangular nesting layouts.

Uses PyQt6 QPainter to draw sheet outlines and part placements from a NestingJob.
Cross-platform, no extra dependencies.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pymodeler.core.nesting import NestingJob


class NestingPreviewWidget(QWidget):
    """Paints one or more sheet layouts from a NestingJob.

    Scales to fit the widget while preserving aspect. Draws sheet border,
    placements as filled rectangles with labels, and yield info.
    """

    def __init__(self, job: Optional[NestingJob] = None, parent=None) -> None:
        super().__init__(parent)
        self.job = job
        self.setMinimumSize(400, 300)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(240, 240, 240))
        self.setPalette(pal)

    def set_job(self, job: NestingJob) -> None:
        self.job = job
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        if self.job is None or not self.job.layouts:
            painter = QPainter(self)
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No nesting layout")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw each sheet stacked vertically with margin
        margin = 20
        y_offset = margin
        widget_w = self.width() - 2 * margin

        for layout in self.job.layouts:
            sw = float(layout.get("sheet_width") or self.job.sheet_width)
            sh = float(layout.get("sheet_height") or self.job.sheet_height)
            if sw <= 0 or sh <= 0:
                continue

            # Scale to available width
            scale = widget_w / sw if sw > 0 else 1.0
            sheet_px_h = int(sh * scale)
            sheet_rect = QRectF(margin, y_offset, widget_w, sheet_px_h)

            # Sheet background + border
            painter.setPen(QPen(QColor(40, 40, 40), 2))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawRect(sheet_rect)

            # Placements
            colors = [
                QColor(100, 150, 220, 180),
                QColor(220, 150, 100, 180),
                QColor(100, 200, 140, 180),
                QColor(200, 100, 180, 180),
                QColor(180, 180, 100, 180),
            ]
            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)

            for i, p in enumerate(layout.get("placements", [])):
                px = margin + p["x"] * scale
                py = y_offset + p["y"] * scale
                pw = p["width"] * scale
                ph = p["height"] * scale
                prect = QRectF(px, py, pw, ph)
                color = colors[i % len(colors)]
                painter.setPen(QPen(color.darker(130), 1))
                painter.setBrush(QBrush(color))
                painter.drawRect(prect)

                # Label
                name = p.get("name") or p.get("part_id") or ""
                if name and pw > 20 and ph > 12:
                    painter.setPen(QColor(20, 20, 20))
                    painter.drawText(prect, Qt.AlignmentFlag.AlignCenter, name[:12])

            # Sheet info
            info = (
                f"Sheet {layout.get('sheet_index', 0) + 1}"
                f"{(' (' + layout['sheet_name'] + ')') if layout.get('sheet_name') else ''}"
                f"  yield {layout.get('yield', 0)*100:.1f}%  "
                f"remnant {layout.get('remnant_area', 0):.0f}"
            )
            painter.setPen(QColor(60, 60, 60))
            painter.drawText(
                QRectF(margin, y_offset + sheet_px_h + 2, widget_w, 16),
                Qt.AlignmentFlag.AlignLeft,
                info,
            )

            y_offset += sheet_px_h + 28

        # Resize hint: set preferred height
        self.setMinimumHeight(max(300, y_offset + margin))


class NestingPreviewDialog(QDialog):
    """Modal dialog showing a NestingJob preview + summary text."""

    def __init__(self, job: NestingJob, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Nesting Preview – {job.name}")
        self.resize(700, 600)

        layout = QVBoxLayout(self)

        summary = QLabel(job.summary())
        summary.setWordWrap(True)
        summary.setStyleSheet("font-family: monospace; padding: 6px;")
        layout.addWidget(summary)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        preview = NestingPreviewWidget(job)
        scroll.setWidget(preview)
        layout.addWidget(scroll, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


def show_nesting_preview(job: NestingJob, parent=None) -> None:
    """Convenience launcher. Packs if layouts empty."""
    if not job.layouts:
        try:
            job.pack()
        except Exception:
            pass
    dlg = NestingPreviewDialog(job, parent)
    dlg.exec()
