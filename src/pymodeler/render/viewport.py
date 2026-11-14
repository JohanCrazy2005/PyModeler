"""OpenGL viewport widget for PyModeler using moderngl + PyQt6.

Draws a ground grid, RGB axes, and scene meshes with a basic orbit camera.
Falls back gracefully when OpenGL is unavailable (e.g. headless CI).
"""

from __future__ import annotations

import math
from typing import Optional, List, Tuple

import numpy as np

from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QWheelEvent, QSurfaceFormat
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

try:
    import moderngl
except ImportError:  # pragma: no cover
    moderngl = None

from pymodeler.core.scene import Scene, SceneObject, Transform


# ---------------------------------------------------------------------------
# Simple orbit camera
# ---------------------------------------------------------------------------

class OrbitCamera:
    """Spherical orbit camera around a target point."""

    def __init__(self) -> None:
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.distance = 8.0
        self.azimuth = 45.0   # degrees, around Y
        self.elevation = 30.0  # degrees, from XZ plane
        self.fov = 45.0
        self.near = 0.1
        self.far = 500.0

    def eye(self) -> np.ndarray:
        az = math.radians(self.azimuth)
        el = math.radians(self.elevation)
        x = self.distance * math.cos(el) * math.sin(az)
        y = self.distance * math.sin(el)
        z = self.distance * math.cos(el) * math.cos(az)
        return self.target + np.array([x, y, z], dtype=np.float32)

    def view_matrix(self) -> np.ndarray:
        eye = self.eye()
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        return _look_at(eye, self.target, up)

    def projection_matrix(self, aspect: float) -> np.ndarray:
        return _perspective(self.fov, aspect, self.near, self.far)

    def orbit(self, d_az: float, d_el: float) -> None:
        self.azimuth += d_az
        self.elevation = max(-89.0, min(89.0, self.elevation + d_el))

    def pan(self, dx: float, dy: float) -> None:
        # Move target in camera right / up directions
        eye = self.eye()
        forward = self.target - eye
        forward = forward / (np.linalg.norm(forward) + 1e-8)
        right = np.cross(forward, np.array([0.0, 1.0, 0.0], dtype=np.float32))
        right = right / (np.linalg.norm(right) + 1e-8)
        up = np.cross(right, forward)
        scale = self.distance * 0.002
        self.target += right * dx * scale + up * (-dy) * scale

    def zoom(self, delta: float) -> None:
        factor = 1.0 - delta * 0.001
        self.distance = max(0.5, min(200.0, self.distance * factor))


def _look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    f = target - eye
    f = f / (np.linalg.norm(f) + 1e-8)
    s = np.cross(f, up)
    s = s / (np.linalg.norm(s) + 1e-8)
    u = np.cross(s, f)
    m = np.eye(4, dtype=np.float32)
    m[0, :3] = s
    m[1, :3] = u
    m[2, :3] = -f
    m[0, 3] = -np.dot(s, eye)
    m[1, 3] = -np.dot(u, eye)
    m[2, 3] = np.dot(f, eye)
    return m


def _perspective(fov_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_deg) / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def _transform_matrix(t: Transform) -> np.ndarray:
    """Build model matrix from location / euler rotation (XYZ degrees) / scale."""
    sx, sy, sz = t.scale
    S = np.diag([sx, sy, sz, 1.0]).astype(np.float32)

    rx, ry, rz = [math.radians(a) for a in t.rotation]
    cx, sx_ = math.cos(rx), math.sin(rx)
    cy, sy_ = math.cos(ry), math.sin(ry)
    cz, sz_ = math.cos(rz), math.sin(rz)

    # XYZ order
    Rx = np.array([
        [1, 0, 0, 0],
        [0, cx, -sx_, 0],
        [0, sx_, cx, 0],
        [0, 0, 0, 1],
    ], dtype=np.float32)
    Ry = np.array([
        [cy, 0, sy_, 0],
        [0, 1, 0, 0],
        [-sy_, 0, cy, 0],
        [0, 0, 0, 1],
    ], dtype=np.float32)
    Rz = np.array([
        [cz, -sz_, 0, 0],
        [sz_, cz, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ], dtype=np.float32)
    R = Rz @ Ry @ Rx

    T = np.eye(4, dtype=np.float32)
    T[0, 3], T[1, 3], T[2, 3] = t.location

    return T @ R @ S


# ---------------------------------------------------------------------------
# Shaders (simple flat color)
# ---------------------------------------------------------------------------

VERTEX_SHADER = """
#version 330
uniform mat4 mvp;
in vec3 in_position;
void main() {
    gl_Position = mvp * vec4(in_position, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330
uniform vec3 color;
out vec4 fragColor;
void main() {
    fragColor = vec4(color, 1.0);
}
"""


# ---------------------------------------------------------------------------
# Viewport widget
# ---------------------------------------------------------------------------

class ViewportWidget(QOpenGLWidget):
    """3D viewport that renders the given Scene with an orbit camera."""

    scene_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        # Request a decent OpenGL context
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setDepthBufferSize(24)
        fmt.setSamples(4)
        QSurfaceFormat.setDefaultFormat(fmt)

        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.camera = OrbitCamera()
        self._scene: Optional[Scene] = None
        self._ctx: Optional["moderngl.Context"] = None
        self._prog = None
        self._grid_vbo = None
        self._grid_vao = None
        self._axes_vbo = None
        self._axes_vao = None
        self._mesh_vaos: List[Tuple] = []  # (vao, vertex_count, color)
        self._last_mouse: Optional[QPoint] = None
        self._gl_ready = False
        self._fallback = False

    def set_scene(self, scene: Optional[Scene]) -> None:
        self._scene = scene
        if self._gl_ready:
            self._rebuild_mesh_geometry()
            self.update()

    def initializeGL(self) -> None:
        if moderngl is None:
            self._fallback = True
            return
        try:
            self._ctx = moderngl.create_context()
            self._ctx.enable(moderngl.DEPTH_TEST)
            self._ctx.enable(moderngl.BLEND)
            self._prog = self._ctx.program(
                vertex_shader=VERTEX_SHADER,
                fragment_shader=FRAGMENT_SHADER,
            )
            self._build_grid()
            self._build_axes()
            self._rebuild_mesh_geometry()
            self._gl_ready = True
        except Exception as exc:  # pragma: no cover
            # OpenGL not available (common in headless CI)
            print(f"Viewport OpenGL init failed, using fallback: {exc}")
            self._fallback = True
            self._gl_ready = False

    def resizeGL(self, w: int, h: int) -> None:
        if self._ctx and not self._fallback:
            self._ctx.viewport = (0, 0, w, h)

    def paintGL(self) -> None:
        if self._fallback or not self._gl_ready or self._ctx is None:
            # Clear to dark gray so the widget still looks intentional
            from PyQt6.QtGui import QPainter, QColor
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(42, 42, 42))
            painter.setPen(QColor(170, 170, 170))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "Viewport\n(OpenGL unavailable in this environment)")
            painter.end()
            return

        self._ctx.clear(0.15, 0.15, 0.16, 1.0)
        aspect = self.width() / max(1, self.height())
        proj = self.camera.projection_matrix(aspect)
        view = self.camera.view_matrix()
        mvp_base = proj @ view

        # Grid
        self._draw_lines(self._grid_vao, mvp_base, (0.35, 0.35, 0.38), 1)

        # Axes
        self._draw_axes(mvp_base)

        # Meshes
        for vao, count, color, model in self._mesh_vaos:
            mvp = mvp_base @ model
            self._prog["mvp"].write(mvp.T.tobytes())
            self._prog["color"].value = color
            vao.render(moderngl.TRIANGLES, vertices=count)

    def _draw_lines(self, vao, mvp, color, width: int = 1) -> None:
        if vao is None:
            return
        self._prog["mvp"].write(mvp.T.tobytes())
        self._prog["color"].value = color
        # Line width is limited on core profile; ignore width
        vao.render(moderngl.LINES)

    def _draw_axes(self, mvp) -> None:
        if self._axes_vao is None:
            return
        # X red, Y green, Z blue – drawn as three separate segments
        self._prog["mvp"].write(mvp.T.tobytes())
        # X
        self._prog["color"].value = (0.9, 0.2, 0.2)
        self._axes_vao.render(moderngl.LINES, first=0, vertices=2)
        # Y
        self._prog["color"].value = (0.2, 0.9, 0.2)
        self._axes_vao.render(moderngl.LINES, first=2, vertices=2)
        # Z
        self._prog["color"].value = (0.2, 0.4, 0.9)
        self._axes_vao.render(moderngl.LINES, first=4, vertices=2)

    def _build_grid(self, size: float = 10.0, divisions: int = 20) -> None:
        step = size / divisions
        lines = []
        for i in range(-divisions, divisions + 1):
            t = i * step
            # lines parallel to X
            lines.extend([[-size, 0.0, t], [size, 0.0, t]])
            # lines parallel to Z
            lines.extend([[t, 0.0, -size], [t, 0.0, size]])
        data = np.array(lines, dtype=np.float32)
        self._grid_vbo = self._ctx.buffer(data.tobytes())
        self._grid_vao = self._ctx.simple_vertex_array(
            self._prog, self._grid_vbo, "in_position"
        )

    def _build_axes(self, length: float = 2.0) -> None:
        # 3 lines: origin->X, origin->Y, origin->Z
        data = np.array([
            [0, 0, 0], [length, 0, 0],
            [0, 0, 0], [0, length, 0],
            [0, 0, 0], [0, 0, length],
        ], dtype=np.float32)
        self._axes_vbo = self._ctx.buffer(data.tobytes())
        self._axes_vao = self._ctx.simple_vertex_array(
            self._prog, self._axes_vbo, "in_position"
        )

    def _rebuild_mesh_geometry(self) -> None:
        self._mesh_vaos.clear()
        if self._scene is None or self._ctx is None:
            return

        # Simple fixed palette for objects
        palette = [
            (0.7, 0.7, 0.75),
            (0.6, 0.75, 0.85),
            (0.8, 0.7, 0.6),
            (0.65, 0.8, 0.65),
            (0.8, 0.65, 0.75),
        ]

        for idx, obj in enumerate(self._scene.objects):
            if not obj.visible:
                continue
            mesh = obj.mesh
            if not mesh.vertices or not mesh.faces:
                continue

            # Triangulate faces
            verts = np.array(mesh.vertices, dtype=np.float32)
            tri_indices = []
            for face in mesh.faces:
                if len(face) < 3:
                    continue
            for i in range(1, len(face) - 1):
                    tri_indices.extend([face[0], face[i], face[i + 1]])

            if not tri_indices:
                continue

            # Expand to per-vertex positions for the triangles
            positions = verts[tri_indices]
            vbo = self._ctx.buffer(positions.astype(np.float32).tobytes())
            vao = self._ctx.simple_vertex_array(self._prog, vbo, "in_position")
            color = palette[idx % len(palette)]
            model = _transform_matrix(obj.transform)
            self._mesh_vaos.append((vao, len(tri_indices), color, model))

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._last_mouse = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._last_mouse is None:
            return
        pos = event.position().toPoint()
        dx = pos.x() - self._last_mouse.x()
        dy = pos.y() - self._last_mouse.y()
        buttons = event.buttons()
        modifiers = event.modifiers()

        if buttons & Qt.MouseButton.MiddleButton or (
            buttons & Qt.MouseButton.LeftButton and modifiers & Qt.KeyboardModifier.AltModifier
        ):
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                self.camera.pan(dx, dy)
            else:
                self.camera.orbit(dx * 0.4, -dy * 0.4)
            self.update()
        elif buttons & Qt.MouseButton.LeftButton:
            # Default left-drag also orbits (Blender-like middle is preferred,
            # but left is more discoverable for first-time users)
            self.camera.orbit(dx * 0.4, -dy * 0.4)
            self.update()

        self._last_mouse = pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._last_mouse = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        self.camera.zoom(delta)
        self.update()
        super().wheelEvent(event)
