"""OpenGL viewport widget for PyModeler using moderngl + QOpenGLWidget.

Features:
- Orbit / pan / zoom camera
- Ground grid and RGB axes
- Mesh drawing with flat shading (computed normals) or wireframe
- Selection highlighting
- Frame selected / frame all
- Click-to-select via raycast against object bounding boxes
- Transform gizmos (translate / rotate / scale) for selected objects
"""

from __future__ import annotations

import math
from typing import Optional, List, Tuple

import numpy as np
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QWheelEvent, QKeyEvent
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
    transform_committed = pyqtSignal(object, object, object)  # obj, old_transform, new_transform

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._scene = None
        self.camera = Camera()
        self.wireframe = False
        self.show_normals = False
        self.show_edges = False
        self.gizmo_mode = "translate"  # "translate", "rotate", "scale"
        self._ctx: Optional["moderngl.Context"] = None
        self._prog = None
        self._prog_unlit = None
        self._grid_vbo = None
        self._grid_vao = None
        self._axes_vbo = None
        self._axes_vao = None
        self._last_mouse: Optional[QPoint] = None
        self._dragging = False
        self._gizmo_dragging = False
        self._gizmo_axis: Optional[int] = None  # 0=x, 1=y, 2=z
        self._drag_start_mouse: Optional[QPoint] = None
        self._drag_start_transform: Optional[object] = None  # Transform copy
        self._click_threshold = 4  # pixels
        self.setMinimumSize(200, 200)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @property
    def scene(self):
        return self._scene

    def set_scene(self, scene) -> None:
        self._scene = scene
        self.update()

    def toggle_wireframe(self) -> None:
        self.wireframe = not self.wireframe
        self.update()

    def toggle_normals(self) -> None:
        """Toggle visual face-normal overlay."""
        self.show_normals = not self.show_normals
        self.update()

    def toggle_edges(self) -> None:
        """Toggle edge overlay (useful with solid shading)."""
        self.show_edges = not self.show_edges
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
        self._draw_gizmo(mvp)

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
        # Build interleaved vertex data: pos(3) + normal(3) + color(3) in local space
        verts = []
        color = (1.0, 0.4, 0.2) if self._scene.is_selected(obj) else (0.7, 0.75, 0.8)
        for face in mesh.faces:
            if len(face) < 3:
                continue
            # Compute flat normal (local)
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
                    p = np.array(mesh.vertices[idx], dtype=np.float32)
                    verts.extend(p.tolist())
                    verts.extend(n.tolist())
                    verts.extend(color)
        if not verts and not self.wireframe:
            return
        model = self._model_matrix(obj.transform)
        if self.wireframe:
            # Build unique edges for wireframe (local)
            edges = set()
            for face in mesh.faces:
                for i in range(len(face)):
                    a, b = face[i], face[(i + 1) % len(face)]
                    edges.add((min(a, b), max(a, b)))
            line_verts = []
            for a, b in edges:
                for idx in (a, b):
                    p = np.array(mesh.vertices[idx], dtype=np.float32)
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
        # mvp already includes view/proj; apply model in shader via uniform, but positions are local
        # so full mvp_model = mvp @ model
        mvp_model = mvp @ model
        self._prog["mvp"].write(mvp_model.tobytes())
        self._prog["model"].write(model.tobytes())
        vao.render(mode)
        vbo.release()
        vao.release()

        # Optional normal overlay
        if self.show_normals:
            self._draw_normals(obj, mvp, model)

        # Optional edge overlay (in addition to wireframe mode)
        if self.show_edges and not self.wireframe:
            self._draw_edges(obj, mvp, model, color)

    def _model_matrix(self, transform) -> np.ndarray:
        """Build column-major model matrix from Transform (loc, Euler XYZ, scale)."""
        loc = np.array(transform.location, dtype=np.float32)
        rot = np.array(transform.rotation, dtype=np.float32)
        scale = np.array(transform.scale, dtype=np.float32)
        # Rotation matrices (XYZ Euler)
        cx, sx = math.cos(rot[0]), math.sin(rot[0])
        cy, sy = math.cos(rot[1]), math.sin(rot[1])
        cz, sz = math.cos(rot[2]), math.sin(rot[2])
        # Rx * Ry * Rz
        r00 = cy * cz
        r01 = -cy * sz
        r02 = sy
        r10 = sx * sy * cz + cx * sz
        r11 = -sx * sy * sz + cx * cz
        r12 = -sx * cy
        r20 = -cx * sy * cz + sx * sz
        r21 = cx * sy * sz + sx * cz
        r22 = cx * cy
        mat = np.eye(4, dtype=np.float32)
        mat[0, 0] = r00 * scale[0]
        mat[0, 1] = r01 * scale[1]
        mat[0, 2] = r02 * scale[2]
        mat[1, 0] = r10 * scale[0]
        mat[1, 1] = r11 * scale[1]
        mat[1, 2] = r12 * scale[2]
        mat[2, 0] = r20 * scale[0]
        mat[2, 1] = r21 * scale[1]
        mat[2, 2] = r22 * scale[2]
        mat[0, 3] = loc[0]
        mat[1, 3] = loc[1]
        mat[2, 3] = loc[2]
        return mat.T  # column-major

    def _rotation_matrix(self, rot: list) -> np.ndarray:
        """Return 3x3 rotation matrix for Euler XYZ (radians)."""
        cx, sx = math.cos(rot[0]), math.sin(rot[0])
        cy, sy = math.cos(rot[1]), math.sin(rot[1])
        cz, sz = math.cos(rot[2]), math.sin(rot[2])
        r00 = cy * cz
        r01 = -cy * sz
        r02 = sy
        r10 = sx * sy * cz + cx * sz
        r11 = -sx * sy * sz + cx * cz
        r12 = -sx * cy
        r20 = -cx * sy * cz + sx * sz
        r21 = cx * sy * sz + sx * cz
        r22 = cx * cy
        return np.array([[r00, r01, r02], [r10, r11, r12], [r20, r21, r22]], dtype=np.float32)

    def _local_axes(self, transform, length: float) -> list:
        """Return world-space offsets for local X/Y/Z axes of the given length."""
        rot = self._rotation_matrix(transform.rotation)
        return [
            rot @ np.array([length, 0.0, 0.0], dtype=np.float32),
            rot @ np.array([0.0, length, 0.0], dtype=np.float32),
            rot @ np.array([0.0, 0.0, length], dtype=np.float32),
        ]

    def _draw_normals(self, obj, mvp: np.ndarray, model: np.ndarray) -> None:
        """Draw face normal lines from face centroids (local space)."""
        if self._ctx is None or self._prog_unlit is None:
            return
        mesh = obj.mesh
        length = max(0.3, self.camera.distance * 0.05)
        lines = []
        for fi, face in enumerate(mesh.faces):
            if len(face) < 3:
                continue
            # Centroid
            pts = [np.array(mesh.vertices[vi], dtype=np.float32) for vi in face]
            centroid = np.mean(pts, axis=0)
            normal = np.array(mesh.compute_face_normal(fi), dtype=np.float32)
            tip = centroid + normal * length
            lines.extend([*centroid, *tip])
        if not lines:
            return
        data = np.array(lines, dtype=np.float32)
        vbo = self._ctx.buffer(data.tobytes())
        vao = self._ctx.simple_vertex_array(self._prog_unlit, vbo, "in_position")
        mvp_model = mvp @ model
        self._prog_unlit["mvp"].write(mvp_model.tobytes())
        self._prog_unlit["color"].value = (0.2, 1.0, 0.4)  # green normals
        self._ctx.line_width = 1.5
        vao.render(moderngl.LINES)
        vbo.release()
        vao.release()

    def _draw_edges(self, obj, mvp: np.ndarray, model: np.ndarray, color: tuple) -> None:
        """Draw edge overlay lines."""
        if self._ctx is None or self._prog_unlit is None:
            return
        mesh = obj.mesh
        edges = set()
        for face in mesh.faces:
            for i in range(len(face)):
                a, b = face[i], face[(i + 1) % len(face)]
                edges.add((min(a, b), max(a, b)))
        line_verts = []
        for a, b in edges:
            for idx in (a, b):
                p = np.array(mesh.vertices[idx], dtype=np.float32)
                line_verts.extend(p.tolist())
        if not line_verts:
            return
        data = np.array(line_verts, dtype=np.float32)
        vbo = self._ctx.buffer(data.tobytes())
        vao = self._ctx.simple_vertex_array(self._prog_unlit, vbo, "in_position")
        mvp_model = mvp @ model
        self._prog_unlit["mvp"].write(mvp_model.tobytes())
        self._prog_unlit["color"].value = tuple(min(1.0, c * 0.6) for c in color)  # darker edges
        self._ctx.line_width = 1.0
        vao.render(moderngl.LINES)
        vbo.release()
        vao.release()

    def _draw_gizmo(self, mvp: np.ndarray) -> None:
        """Draw oriented axis gizmo for the primary selected object.

        Active (dragged) axis is drawn brighter and thicker for visual feedback.
        """
        if self._scene is None or self._ctx is None or self._prog_unlit is None:
            return
        selected = self._scene.selected_objects()
        if not selected:
            return
        obj = selected[0]
        loc = np.array(obj.transform.location, dtype=np.float32)
        length = max(0.5, self.camera.distance * 0.15)
        offsets = self._local_axes(obj.transform, length)
        colors = [
            (1.0, 0.2, 0.2),  # X red
            (0.2, 1.0, 0.2),  # Y green
            (0.2, 0.4, 1.0),  # Z blue
        ]
        for i, (offset, base_color) in enumerate(zip(offsets, colors)):
            tip = loc + offset
            is_active = self._gizmo_dragging and self._gizmo_axis == i
            color = tuple(min(1.0, c * 1.6) for c in base_color) if is_active else base_color
            line_w = 6.0 if is_active else 3.0
            data = np.array([*loc, *tip], dtype=np.float32)
            vbo = self._ctx.buffer(data.tobytes())
            vao = self._ctx.simple_vertex_array(self._prog_unlit, vbo, "in_position")
            self._prog_unlit["mvp"].write(mvp.tobytes())
            self._prog_unlit["color"].value = color
            self._ctx.line_width = line_w
            vao.render(moderngl.LINES)
            vbo.release()
            vao.release()
        # Optional arrowheads could be added later

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._last_mouse = event.pos()
        self._dragging = False
        self._gizmo_dragging = False
        self._gizmo_axis = None
        # Check gizmo hit first (if something is selected)
        if self._scene and self._scene.selected_objects():
            axis = self._hit_gizmo(event.pos().x(), event.pos().y())
            if axis is not None:
                self._gizmo_dragging = True
                self._gizmo_axis = axis
                self._drag_start_mouse = event.pos()
                obj = self._scene.selected_objects()[0]
                # Snapshot current transform
                from pymodeler.core.scene import Transform
                self._drag_start_transform = Transform(
                    location=list(obj.transform.location),
                    rotation=list(obj.transform.rotation),
                    scale=list(obj.transform.scale),
                )
                return

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._last_mouse is None:
            return
        dx = event.pos().x() - self._last_mouse.x()
        dy = event.pos().y() - self._last_mouse.y()
        if self._gizmo_dragging and self._gizmo_axis is not None and self._scene:
            self._apply_gizmo_drag(event.pos())
            self._last_mouse = event.pos()
            self.update()
            return
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
        if self._gizmo_dragging and self._drag_start_transform is not None and self._scene:
            obj = self._scene.selected_objects()[0] if self._scene.selected_objects() else None
            if obj is not None:
                # Commit the change
                from pymodeler.core.scene import Transform
                new_t = Transform(
                    location=list(obj.transform.location),
                    rotation=list(obj.transform.rotation),
                    scale=list(obj.transform.scale),
                )
                self.transform_committed.emit(obj, self._drag_start_transform, new_t)
            self._gizmo_dragging = False
            self._gizmo_axis = None
            self._drag_start_transform = None
            self._last_mouse = None
            self._dragging = False
            return
        if not self._dragging and self._scene is not None:
            self._click_select(event.pos())
        self._last_mouse = None
        self._dragging = False

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key.Key_G:
            self.gizmo_mode = "translate"
            self.update()
        elif key == Qt.Key.Key_R:
            self.gizmo_mode = "rotate"
            self.update()
        elif key == Qt.Key.Key_S:
            self.gizmo_mode = "scale"
            self.update()
        else:
            super().keyPressEvent(event)

    def _hit_gizmo(self, x: int, y: int) -> Optional[int]:
        """Return axis index (0/1/2) if click is near a local gizmo axis, else None."""
        if self._scene is None or not self._scene.selected_objects():
            return None
        obj = self._scene.selected_objects()[0]
        loc = np.array(obj.transform.location, dtype=np.float32)
        length = max(0.5, self.camera.distance * 0.15)
        offsets = self._local_axes(obj.transform, length)
        origin_s = self._world_to_screen(loc)
        if origin_s is None:
            return None
        best_axis = None
        best_dist = 12.0  # pixel threshold
        for i, d in enumerate(offsets):
            tip_s = self._world_to_screen(loc + d)
            if tip_s is None:
                continue
            dist = self._point_line_distance(np.array([x, y], dtype=np.float32), origin_s, tip_s)
            if dist < best_dist:
                best_dist = dist
                best_axis = i
        return best_axis

    def _world_to_screen(self, world: np.ndarray) -> Optional[np.ndarray]:
        """Project world point to screen pixels. Returns None if behind camera."""
        w, h = self.width(), self.height()
        if h == 0:
            return None
        view = self.camera.view_matrix()
        proj = self._projection()
        clip = proj @ view @ np.array([*world, 1.0], dtype=np.float32)
        if clip[3] <= 0:
            return None
        ndc = clip[:3] / clip[3]
        sx = (ndc[0] * 0.5 + 0.5) * w
        sy = (1.0 - (ndc[1] * 0.5 + 0.5)) * h
        return np.array([sx, sy], dtype=np.float32)

    @staticmethod
    def _point_line_distance(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
        """Distance from point p to segment ab in 2D."""
        ab = b - a
        ap = p - a
        t = np.dot(ap, ab) / (np.dot(ab, ab) + 1e-8)
        t = max(0.0, min(1.0, t))
        closest = a + t * ab
        return float(np.linalg.norm(p - closest))

    def _apply_gizmo_drag(self, pos: QPoint) -> None:
        if self._scene is None or self._gizmo_axis is None or self._drag_start_transform is None:
            return
        obj = self._scene.selected_objects()[0]
        axis = self._gizmo_axis
        # Compute screen-space direction of the local axis for projection
        loc = np.array(self._drag_start_transform.location, dtype=np.float32)
        length = max(0.5, self.camera.distance * 0.15)
        offsets = self._local_axes(self._drag_start_transform, length)
        axis_dir_world = offsets[axis] / (np.linalg.norm(offsets[axis]) + 1e-8)
        origin_s = self._world_to_screen(loc)
        tip_s = self._world_to_screen(loc + offsets[axis])
        if origin_s is None or tip_s is None:
            # Fallback to simple sensitivity
            sens = self.camera.distance * 0.005
            dx = pos.x() - self._drag_start_mouse.x()
            dy = pos.y() - self._drag_start_mouse.y()
            delta = (dx - dy) * sens
        else:
            screen_dir = tip_s - origin_s
            screen_len = np.linalg.norm(screen_dir) + 1e-8
            mouse_delta = np.array([pos.x() - self._drag_start_mouse.x(),
                                    pos.y() - self._drag_start_mouse.y()], dtype=np.float32)
            # Project mouse movement onto screen axis direction (pixels)
            pixel_delta = np.dot(mouse_delta, screen_dir) / screen_len
            # Approximate world units: use camera distance and a simple scale
            world_per_pixel = self.camera.distance * 0.002
            delta = pixel_delta * world_per_pixel

        if self.gizmo_mode == "translate":
            new_loc = np.array(self._drag_start_transform.location, dtype=np.float32)
            new_loc += delta * axis_dir_world
            obj.transform.location = new_loc.tolist()
        elif self.gizmo_mode == "rotate":
            new_rot = list(self._drag_start_transform.rotation)
            # Rotate around the local axis (simple Euler addition for now)
            new_rot[axis] += delta * 0.5
            obj.transform.rotation = new_rot
        elif self.gizmo_mode == "scale":
            new_scale = list(self._drag_start_transform.scale)
            factor = 1.0 + delta * 0.1
            new_scale[axis] = max(0.01, new_scale[axis] * factor)
            obj.transform.scale = new_scale

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

