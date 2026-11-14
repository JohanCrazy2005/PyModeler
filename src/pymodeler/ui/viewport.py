"""OpenGL viewport widget for PyModeler using PyOpenGL and QOpenGLWidget.

Draws a ground grid, RGB axes, and all visible scene meshes with a basic orbit camera.
"""

from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent, QWheelEvent
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QWidget

try:
    from OpenGL.GL import (
        glClear,
        glClearColor,
        glEnable,
        glDisable,
        glBegin,
        glEnd,
        glVertex3f,
        glColor3f,
        glLineWidth,
        glPolygonMode,
        glMatrixMode,
        glLoadIdentity,
        glTranslatef,
        glRotatef,
        glScalef,
        glViewport,
        glOrtho,
        glFrustum,
        glPushMatrix,
        glPopMatrix,
        GL_COLOR_BUFFER_BIT,
        GL_DEPTH_BUFFER_BIT,
        GL_DEPTH_TEST,
        GL_LINES,
        GL_LINE_STRIP,
        GL_TRIANGLES,
        GL_QUADS,
        GL_PROJECTION,
        GL_MODELVIEW,
        GL_FRONT_AND_BACK,
        GL_LINE,
        GL_FILL,
    )
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False


class ViewportWidget(QOpenGLWidget):
    """Simple orbit-camera OpenGL viewport that renders the Scene."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.scene = None  # set by MainWindow

        # Camera state
        self.azimuth = 45.0  # degrees
        self.elevation = 30.0
        self.distance = 10.0
        self.pan_x = 0.0
        self.pan_y = 0.0

        self._last_mouse: Optional[QPoint] = None
        self._panning = False

        self.setMinimumSize(200, 200)

    def set_scene(self, scene) -> None:
        self.scene = scene
        self.update()

    def initializeGL(self) -> None:
        if not HAS_OPENGL:
            return
        glClearColor(0.15, 0.15, 0.18, 1.0)
        glEnable(GL_DEPTH_TEST)
        glLineWidth(1.5)

    def resizeGL(self, w: int, h: int) -> None:
        if not HAS_OPENGL or h == 0:
            return
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = w / float(h)
        # Simple perspective
        glFrustum(-aspect * 0.5, aspect * 0.5, -0.5, 0.5, 1.0, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self) -> None:
        if not HAS_OPENGL:
            return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Camera transform
        glTranslatef(0.0, 0.0, -self.distance)
        glRotatef(self.elevation, 1.0, 0.0, 0.0)
        glRotatef(self.azimuth, 0.0, 1.0, 0.0)
        glTranslatef(-self.pan_x, -self.pan_y, 0.0)

        self._draw_grid()
        self._draw_axes()
        self._draw_scene()

    def _draw_grid(self) -> None:
        if not HAS_OPENGL:
            return
        glColor3f(0.4, 0.4, 0.45)
        glBegin(GL_LINES)
        size = 20
        step = 1.0
        for i in range(-size, size + 1):
            glVertex3f(i * step, 0.0, -size * step)
            glVertex3f(i * step, 0.0, size * step)
            glVertex3f(-size * step, 0.0, i * step)
            glVertex3f(size * step, 0.0, i * step)
        glEnd()

    def _draw_axes(self) -> None:
        if not HAS_OPENGL:
            return
        glLineWidth(2.5)
        glBegin(GL_LINES)
        glColor3f(1.0, 0.2, 0.2)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(3.0, 0.0, 0.0)
        glColor3f(0.2, 1.0, 0.2)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 3.0, 0.0)
        glColor3f(0.2, 0.2, 1.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 3.0)
        glEnd()
        glLineWidth(1.5)

    def _draw_scene(self) -> None:
        if not HAS_OPENGL or self.scene is None:
            return
        for obj in self.scene.objects:
            if not obj.visible:
                continue
            glPushMatrix()
            loc = obj.transform.location
            glTranslatef(loc[0], loc[1], loc[2])
            self._draw_mesh(obj.mesh)
            glPopMatrix()

    def _draw_mesh(self, mesh) -> None:
        if not HAS_OPENGL:
            return
        glColor3f(0.7, 0.75, 0.8)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        for face in mesh.faces:
            n = len(face)
            if n < 3:
                continue
            if n > 4:
                glBegin(GL_TRIANGLES)
                v0 = mesh.vertices[face[0]]
                for i in range(1, n - 1):
                    v1 = mesh.vertices[face[i]]
                    v2 = mesh.vertices[face[i + 1]]
                    glVertex3f(*v0)
                    glVertex3f(*v1)
                    glVertex3f(*v2)
                glEnd()
            else:
                mode = GL_TRIANGLES if n == 3 else GL_QUADS
                glBegin(mode)
                for idx in face:
                    v = mesh.vertices[idx]
                    glVertex3f(v[0], v[1], v[2])
                glEnd()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._last_mouse = event.pos()
        self._panning = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._last_mouse is None:
            return
        dx = event.pos().x() - self._last_mouse.x()
        dy = event.pos().y() - self._last_mouse.y()
        if self._panning:
            scale = self.distance * 0.002
            self.pan_x += dx * scale
            self.pan_y -= dy * scale
        else:
            self.azimuth += dx * 0.5
            self.elevation += dy * 0.5
            self.elevation = max(-89.0, min(89.0, self.elevation))
        self._last_mouse = event.pos()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._last_mouse = None
        self._panning = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        factor = 0.9 if delta > 0 else 1.1
        self.distance = max(0.5, min(100.0, self.distance * factor))
        self.update()
