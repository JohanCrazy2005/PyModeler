"""OpenGL viewport widget for PyModeler using moderngl + QOpenGLWidget.

Features:
- Orbit / pan / zoom camera
- Ground grid and RGB axes
- Mesh drawing with flat shading (computed normals) or wireframe
- Selection highlighting
- Frame selected / frame all
- Click-to-select via raycast against object bounding boxes
"""

from __future__ import annotations

import math
from typing import Optional, List, Tuple

import numpy as np
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QWheelEvent
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QWidget

try:
    import moderngl
    HAS_MODERNGL = True
except ImportError:
    HAS_MODERNGL = False


class Camera:
    """Simple orbit camera around a target point."""

    def __init__(self) -> None:
        self.azimuth = 45.0  # degrees
        self.elevation = 30.0
        self.distance = 10.0
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.pan_offset = np.array([0.0, 0.0], dtype=np.float32)  # screen-space pan

    def orbit(self, daz: float, delv: float) -> None:
        self.azimuth += daz
        self.elevation = max(-89.0, min(89.0, self.elevation + delv))

    def pan(self, dx: float, dy: float) -> None:
        # Approximate world-space pan
        scale = self.distance * 0.002
        self.pan_offset[0] += dx * scale
        self.pan_offset[1] -= dy * scale

    def zoom(self, delta: float) -> None:
        factor = 0.9 if delta > 0 else 1.1
        self.distance = max(0.5, min(200.0, self.distance * factor))

    def eye_position(self) -> np.ndarray:
        az = math.radians(self.azimuth)
        el = math.radians(self.elevation)
        x = self.distance * math.cos(el) * math.sin(az)
        y = self.distance * math.sin(el)
        z = self.distance * math.cos(el) * math.cos(az)
        return self.target + np.array([x, y, z], dtype=np.float32)

    def view_matrix(self) -> np.ndarray:
        eye = self.eye_position()
        # Simple look-at (up is Y)
        forward = self.target - eye
        forward /= np.linalg.norm(forward) + 1e-8
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        right = np.cross(forward, up)
        right /= np.linalg.norm(right) + 1e-8
        up = np.cross(right, forward)
        # Apply pan in view space
        right *= 1.0
        up *= 1.0
        eye_panned = eye + right * self.pan_offset[0] + up * self.pan_offset[1]
        # Recompute
        forward = self.target - eye_panned
        forward /= np.linalg.norm(forward) + 1e-8
        right = np.cross(forward, up)
        right /= np.linalg.norm(right) + 1e-8
        up = np.cross(right, forward)
        mat = np.eye(4, dtype=np.float32)
        mat[0, :3] = right
        mat[1, :3] = up
        mat[2, :3] = -forward
        mat[0, 3] = -np.dot(right, eye_panned)
        mat[1, 3] = -np.dot(up, eye_panned)
        mat[2, 3] = np.dot(forward, eye_panned)
        return mat.T  # column-major for GL

    def frame_points(self, points: List[np.ndarray], padding: float = 1.5) -> None:
        if not points:
            return
        pts = np.array(points, dtype=np.float32)
        center = pts.mean(axis=0)
        extents = pts.max(axis=0) - pts.min(axis=0)
        radius = max(extents.max(), 1.0) * 0.5 * padding
        self.target = center
        self.distance = max(2.0, radius * 2.5)
        self.pan_offset[:] = 0.0


class ViewportWidget(QOpenGLWidget):
    """moderngl-based orbit viewport."""

    selection_changed = pyqtSignal()  # emitted after click-select so UI can sync

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._scene = None
        self.camera = Camera()
        self.wireframe = False
        self._ctx: Optional["moderngl.Context"] = None
        self._prog = None
        self._prog_unlit = None
        self._grid_vbo = None
        self._grid_vao = None
        self._axes_vbo = None
        self._axes_vao = None
        self._last_mouse: Optional[QPoint] = None
        self._dragging = False
        self._click_threshold = 4  # pixels
        self.setMinimumSize(200, 200)

    @property
    def scene(self):
        return self._scene

    def set_scene(self, scene) -> None:
        self._scene = scene
        self.update()

    def toggle_wireframe(self) -> None:
        self.wireframe = not self.wireframe
        self.update()

    def frame_all(self) -> None:
        if self._scene is None or not self._scene.objects:
            return
        points = []
        for obj in self._scene.objects:
            if not obj.visible:
                continue
            loc = np.array(obj.transform.location, dtype=np.float32)
            # Approximate by mesh bbox + location
            if obj.mesh.vertices:
                verts = np.array(obj.mesh.vertices, dtype=np.float32) + loc
                points.extend(verts.tolist())
        if points:
            self.camera.frame_points([np.array(p) for p in points])
            self.update()

    def frame_selected(self) -> None:
        if self._scene is None:
            return
        selected = self._scene.selected_objects()
        if not selected:
            self.frame_all()
            return
        points = []
        for obj in selected:
            loc = np.array(obj.transform.location, dtype=np.float32)
            if obj.mesh.vertices:
                verts = np.array(obj.mesh.vertices, dtype=np.float32) + loc
                points.extend(verts.tolist())
        if points:
            self.camera.frame_points([np.array(p) for p in points])
            self.update()

    def initializeGL(self) -> None:
        if not HAS_MODERNGL:
            return
        try:
            self._ctx = moderngl.create_context()
            self._ctx.enable(moderngl.DEPTH_TEST)
            # Simple shader: position + normal -> diffuse lighting
            self._prog = self._ctx.program(
                vertex_shader="""
                    #version 330
                    in vec3 in_position;
                    in vec3 in_normal;
                    in vec3 in_color;
                    uniform mat4 mvp;
                    uniform mat4 model;
                    out vec3 v_normal;
                    out vec3 v_color;
                    void main() {
                        gl_Position = mvp * vec4(in_position, 1.0);
                        v_normal = mat3(model) * in_normal;
                        v_color = in_color;
                    }
                """,
                fragment_shader="""
                    #version 330
                    in vec3 v_normal;
                    in vec3 v_color;
                    out vec4 f_color;
                    void main() {
                        vec3 n = normalize(v_normal);
                        vec3 light = normalize(vec3(0.5, 1.0, 0.8));
                        float diff = max(dot(n, light), 0.15);
                        f_color = vec4(v_color * diff, 1.0);
                    }
                """,
            )
            # Simple unlit program for grid / axes
            self._prog_unlit = self._ctx.program(
                vertex_shader="""
                    #version 330
                    in vec3 in_position;
                    uniform mat4 mvp;
                    void main() {
                        gl_Position = mvp * vec4(in_position, 1.0);
                    }
                """,
                fragment_shader="""
                    #version 330
                    uniform vec3 color;
                    out vec4 f_color;
                    void main() {
                        f_color = vec4(color, 1.0);
                    }
                """,
            )
            self._build_static_geometry()
        except Exception:
            self._ctx = None

    def _build_static_geometry(self) -> None:
        if self._ctx is None:
            return
        # Grid
        size = 20
        step = 1.0
        grid_verts = []
        for i in range(-size, size + 1):
            grid_verts.extend([i * step, 0.0, -size * step, i * step, 0.0, size * step])
            grid_verts.extend([-size * step, 0.0, i * step, size * step, 0.0, i * step])
        grid_data = np.array(grid_verts, dtype=np.float32)
        self._grid_vbo = self._ctx.buffer(grid_data.tobytes())
        self._grid_vao = self._ctx.simple_vertex_array(self._prog_unlit, self._grid_vbo, "in_position")

        # Axes
        axes = np.array([
            0, 0, 0, 3, 0, 0,
            0, 0, 0, 0, 3, 0,
            0, 0, 0, 0, 0, 3,
        ], dtype=np.float32)
        self._axes_vbo = self._ctx.buffer(axes.tobytes())
        self._axes_vao = self._ctx.simple_vertex_array(self._prog_unlit, self._axes_vbo, "in_position")

    def resizeGL(self, w: int, h: int) -> None:
        if self._ctx is None or h == 0:
            return
        self._ctx.viewport = (0, 0, w, h)

    def paintGL(self) -> None:
        if self._ctx is None:
            return
        self._ctx.clear(0.15, 0.15, 0.18)
        mvp = self._projection() @ self.camera.view_matrix()
        # Unlit grid
        self._prog_unlit["mvp"].write(mvp.tobytes())
        self._prog_unlit["color"].value = (0.4, 0.4, 0.45)
        if self._grid_vao:
            self._ctx.line_width = 1.0
            self._grid_vao.render(moderngl.LINES)

        # Axes colored separately would need per-vertex; draw with red for now or split
        self._prog_unlit["color"].value = (1.0, 0.2, 0.2)
        if self._axes_vao:
            self._ctx.line_width = 2.0
            self._axes_vao.render(moderngl.LINES)

        self._draw_scene(mvp)

    def _projection(self) -> np.ndarray:
        w, h = self.width(), self.height()
        aspect = w / float(h) if h else 1.0
        fov = math.radians(45.0)
        near, far = 0.1, 200.0
        f = 1.0 / math.tan(fov / 2.0)
        proj = np.zeros((4, 4), dtype=np.float32)
        proj[0, 0] = f / aspect
        proj[1, 1] = f
        proj[2, 2] = (far + near) / (near - far)
        proj[2, 3] = (2 * far * near) / (near - far)
        proj[3, 2] = -1.0
        return proj

    def _draw_scene(self, mvp: np.ndarray) -> None:
        if self._scene is None or self._ctx is None:
            return
        for obj in self._scene.objects:
            if not obj.visible:
                continue
            self._draw_mesh(obj, mvp)

    def _draw_mesh(self, obj, mvp: np.ndarray) -> None:
        mesh = obj.mesh
        if not mesh.vertices or not mesh.faces:
            return
        # Build interleaved vertex data: pos(3) + normal(3) + color(3)
        verts = []
        color = (1.0, 0.4, 0.2) if self._scene.is_selected(obj) else (0.7, 0.75, 0.8)
        loc = np.array(obj.transform.location, dtype=np.float32)
        for face in mesh.faces:
            if len(face) < 3:
                continue
            # Compute flat normal
            v0 = np.array(mesh.vertices[face[0]], dtype=np.float32)
            v1 = np.array(mesh.vertices[face[1]], dtype=np.float32)
            v2 = np.array(mesh.vertices[face[2]], dtype=np.float32)
            n = np.cross(v1 - v0, v2 - v0)
            n_len = np.linalg.norm(n)
            if n_len > 1e-8:
                n /= n_len
            else:
                n = np.array([0.0, 1.0, 0.0], dtype=np.float32)
            # Fan triangulate if needed
            for i in range(1, len(face) - 1):
                for idx in (face[0], face[i], face[i + 1]):
                    p = np.array(mesh.vertices[idx], dtype=np.float32) + loc
                    verts.extend(p.tolist())
                    verts.extend(n.tolist())
                    verts.extend(color)
        if not verts and not self.wireframe:
            return
        if self.wireframe:
            # Build unique edges for wireframe
            edges = set()
            for face in mesh.faces:
                for i in range(len(face)):
                    a, b = face[i], face[(i + 1) % len(face)]
                    edges.add((min(a, b), max(a, b)))
            line_verts = []
            for a, b in edges:
                for idx in (a, b):
                    p = np.array(mesh.vertices[idx], dtype=np.float32) + loc
                    line_verts.extend(p.tolist())
                    line_verts.extend([0, 1, 0])  # dummy normal
                    line_verts.extend(color)
            if not line_verts:
                return
            data = np.array(line_verts, dtype=np.float32)
            mode = moderngl.LINES
        else:
            data = np.array(verts, dtype=np.float32)
            mode = moderngl.TRIANGLES
        vbo = self._ctx.buffer(data.tobytes())
        vao = self._ctx.simple_vertex_array(self._prog, vbo, "in_position", "in_normal", "in_color")
        ident = np.eye(4, dtype=np.float32)
        self._prog["mvp"].write(mvp.tobytes())
        self._prog["model"].write(ident.tobytes())
        vao.render(mode)
        vbo.release()
        vao.release()

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._last_mouse = event.pos()
        self._dragging = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._last_mouse is None:
            return
        dx = event.pos().x() - self._last_mouse.x()
        dy = event.pos().y() - self._last_mouse.y()
        if abs(dx) + abs(dy) > self._click_threshold:
            self._dragging = True
        if self._dragging:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.camera.pan(dx, dy)
            else:
                self.camera.orbit(dx * 0.5, dy * 0.5)
            self._last_mouse = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self._dragging and self._scene is not None:
            self._click_select(event.pos())
        self._last_mouse = None
        self._dragging = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        self.camera.zoom(event.angleDelta().y())
        self.update()

    def _click_select(self, pos: QPoint) -> None:
        """Simple raycast against object AABBs for object-mode selection."""
        if self._scene is None or self._ctx is None:
            return
        # Unproject click to world ray
        ray_o, ray_d = self._screen_to_ray(pos.x(), pos.y())
        best = None
        best_t = float("inf")
        for obj in self._scene.objects:
            if not obj.visible or not obj.mesh.vertices:
                continue
            loc = np.array(obj.transform.location, dtype=np.float32)
            verts = np.array(obj.mesh.vertices, dtype=np.float32) + loc
            mn = verts.min(axis=0)
            mx = verts.max(axis=0)
            # Expand a bit
            mn -= 0.05
            mx += 0.05
            t = self._ray_aabb(ray_o, ray_d, mn, mx)
            if t is not None and t < best_t:
                best_t = t
                best = obj
        if best is not None:
            self._scene.select(best, clear=True)
            self.selection_changed.emit()
            self.update()

    def _screen_to_ray(self, x: int, y: int) -> Tuple[np.ndarray, np.ndarray]:
        w, h = self.width(), self.height()
        # NDC
        ndc_x = (2.0 * x / w) - 1.0
        ndc_y = 1.0 - (2.0 * y / h)
        proj = self._projection()
        view = self.camera.view_matrix()
        inv_vp = np.linalg.inv(proj @ view)
        near = inv_vp @ np.array([ndc_x, ndc_y, -1.0, 1.0], dtype=np.float32)
        far = inv_vp @ np.array([ndc_x, ndc_y, 1.0, 1.0], dtype=np.float32)
        near /= near[3]
        far /= far[3]
        origin = near[:3]
        direction = far[:3] - near[:3]
        direction /= np.linalg.norm(direction) + 1e-8
        return origin, direction

    @staticmethod
    def _ray_aabb(o: np.ndarray, d: np.ndarray, mn: np.ndarray, mx: np.ndarray) -> Optional[float]:
        tmin = 0.0
        tmax = float("inf")
        for i in range(3):
            if abs(d[i]) < 1e-8:
                if o[i] < mn[i] or o[i] > mx[i]:
                    return None
                continue
            t1 = (mn[i] - o[i]) / d[i]
            t2 = (mx[i] - o[i]) / d[i]
            tmin = max(tmin, min(t1, t2))
            tmax = min(tmax, max(t1, t2))
        if tmin > tmax or tmax < 0:
            return None
        return tmin if tmin >= 0 else tmax
