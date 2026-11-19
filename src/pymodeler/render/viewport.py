"""OpenGL viewport widget for PyModeler using moderngl + QOpenGLWidget.

Features:
- Orbit / pan / zoom camera
- Ground grid and RGB axes
- Mesh drawing with flat shading or wireframe using full object transforms
- Selection highlighting
- Frame selected / frame all (full scale+rot+loc)
- Click-to-select via raycast against transformed object AABBs
- Transform gizmos (translate with arrowheads / rotate with rings / scale markers) for selected objects
"""

from __future__ import annotations

import math
from typing import Optional, List, Tuple

import numpy as np
try:
    from PyQt6.QtCore import Qt, QPoint, pyqtSignal
    from PyQt6.QtGui import QMouseEvent, QWheelEvent, QKeyEvent
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtWidgets import QWidget
    HAS_QT = True
except ImportError:
    HAS_QT = False
    # Stubs so the module can be imported in pure-math tests
    class QOpenGLWidget:  # type: ignore
        pass
    class QWidget:  # type: ignore
        pass
    Qt = type("Qt", (), {"MouseButton": type("MB", (), {"LeftButton": 1}), "Key": type("K", (), {})})()
    QPoint = object
    pyqtSignal = lambda *a, **k: None
    QMouseEvent = object
    QWheelEvent = object
    QKeyEvent = object

try:
    import moderngl
    HAS_MODERNGL = True
except ImportError:
    HAS_MODERNGL = False


def extract_unique_edges(faces: List[List[int]]) -> List[Tuple[int, int]]:
    """Return unique undirected edges from a list of faces (as sorted index pairs)."""
    edges = set()
    for face in faces:
        n = len(face)
        if n < 2:
            continue
        for i in range(n):
            a, b = face[i], face[(i + 1) % n]
            edges.add((min(a, b), max(a, b)))
    return sorted(edges)


def generate_ring_points(center: np.ndarray, normal: np.ndarray, radius: float, segments: int = 24) -> List[np.ndarray]:
    """Pure helper: points on a circle in the plane perpendicular to normal."""
    normal = normal / (np.linalg.norm(normal) + 1e-8)
    if abs(normal[1]) < 0.9:
        side = np.cross(normal, np.array([0.0, 1.0, 0.0], dtype=np.float32))
    else:
        side = np.cross(normal, np.array([1.0, 0.0, 0.0], dtype=np.float32))
    side /= np.linalg.norm(side) + 1e-8
    up = np.cross(normal, side)
    up /= np.linalg.norm(up) + 1e-8
    pts = []
    for k in range(segments):
        ang = k * 2 * math.pi / segments
        p = center + (side * math.cos(ang) + up * math.sin(ang)) * radius
        pts.append(p)
    return pts


def generate_arrow_base_points(tip: np.ndarray, shaft_dir: np.ndarray, radius: float = 0.18, segments: int = 4) -> List[np.ndarray]:
    """Pure helper: base points of an arrowhead cone around shaft_dir ending at tip."""
    shaft_dir = shaft_dir / (np.linalg.norm(shaft_dir) + 1e-8)
    if abs(shaft_dir[1]) < 0.9:
        side = np.cross(shaft_dir, np.array([0.0, 1.0, 0.0], dtype=np.float32))
    else:
        side = np.cross(shaft_dir, np.array([1.0, 0.0, 0.0], dtype=np.float32))
    side /= np.linalg.norm(side) + 1e-8
    up = np.cross(shaft_dir, side)
    up /= np.linalg.norm(up) + 1e-8
    shaft = tip - shaft_dir * 0.25
    pts = []
    for k in range(segments):
        ang = k * 2 * math.pi / segments
        p = shaft + (side * math.cos(ang) + up * math.sin(ang)) * radius
        pts.append(p)
    return pts


def hit_test_gizmo_axis(
    ray_origin: np.ndarray,
    ray_dir: np.ndarray,
    gizmo_origin: np.ndarray,
    axes: List[np.ndarray],
    mode: str = "translate",
    tip_radius: float = 0.35,
    ring_radius: float = 1.2,
    ring_tolerance: float = 0.25,
) -> Optional[int]:
    """Pure, headless-safe gizmo hit test.

    Prefers arrowhead tips for translate, rotation rings for rotate,
    and end markers for scale. Falls back to axis shaft proximity.
    Returns axis index 0/1/2 or None.
    """
    ray_dir = ray_dir / (np.linalg.norm(ray_dir) + 1e-8)
    best_idx: Optional[int] = None
    best_score = float("inf")

    for i, axis in enumerate(axes):
        axis_len = np.linalg.norm(axis)
        if axis_len < 1e-6:
            continue
        axis_dir = axis / axis_len
        end = gizmo_origin + axis

        if mode == "translate":
            # Prefer tip (arrowhead)
            tip_dist = _ray_point_distance(ray_origin, ray_dir, end)
            if tip_dist is not None and tip_dist < tip_radius and tip_dist < best_score:
                best_score = tip_dist
                best_idx = i
            # Shaft as fallback
            shaft_dist = _ray_segment_distance(ray_origin, ray_dir, gizmo_origin, end)
            if shaft_dist is not None and shaft_dist < 0.22 and shaft_dist < best_score:
                best_score = shaft_dist
                best_idx = i

        elif mode == "rotate":
            # Ring: intersect ray with plane perpendicular to axis through origin
            normal = axis_dir
            denom = np.dot(ray_dir, normal)
            if abs(denom) > 1e-6:
                t = np.dot(gizmo_origin - ray_origin, normal) / denom
                if t > 0:
                    hit = ray_origin + ray_dir * t
                    dist_from_center = np.linalg.norm(hit - gizmo_origin)
                    ring_err = abs(dist_from_center - ring_radius)
                    if ring_err < ring_tolerance and ring_err < best_score:
                        best_score = ring_err
                        best_idx = i

        else:  # scale
            marker_dist = _ray_point_distance(ray_origin, ray_dir, end)
            if marker_dist is not None and marker_dist < tip_radius and marker_dist < best_score:
                best_score = marker_dist
                best_idx = i

    return best_idx


def _ray_point_distance(ray_o: np.ndarray, ray_d: np.ndarray, point: np.ndarray) -> Optional[float]:
    """Distance from ray to a point (None if behind ray origin)."""
    to_point = point - ray_o
    t = np.dot(to_point, ray_d)
    if t < 0:
        return None
    closest = ray_o + ray_d * t
    return float(np.linalg.norm(closest - point))


def _ray_segment_distance(ray_o: np.ndarray, ray_d: np.ndarray, a: np.ndarray, b: np.ndarray) -> Optional[float]:
    """Approximate closest distance between ray and line segment AB."""
    v = b - a
    w = ray_o - a
    c1 = np.dot(w, v)
    c2 = np.dot(v, v)
    if c2 < 1e-8:
        return _ray_point_distance(ray_o, ray_d, a)
    t_seg = max(0.0, min(1.0, c1 / c2))
    closest_on_seg = a + t_seg * v
    return _ray_point_distance(ray_o, ray_d, closest_on_seg)


class Camera:
    """Simple orbit camera around a target point."""

    def __init__(self) -> None:
        self.azimuth = 45.0  # degrees
        self.elevation = 30.0
        self.distance = 10.0
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.pan_offset = np.array([0.0, 0.0], dtype=np.float32)
        self.orthographic = False

    def orbit(self, daz: float, delv: float) -> None:
        self.azimuth += daz
        self.elevation = max(-89.0, min(89.0, self.elevation + delv))

    def pan(self, dx: float, dy: float) -> None:
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
        forward = self.target - eye
        forward /= np.linalg.norm(forward) + 1e-8
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        right = np.cross(forward, up)
        right /= np.linalg.norm(right) + 1e-8
        up = np.cross(right, forward)
        eye_panned = eye + right * self.pan_offset[0] + up * self.pan_offset[1]
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
        return mat.T

    def set_standard_view(self, name: str) -> None:
        views = {
            "front": (0.0, 0.0),
            "back": (180.0, 0.0),
            "right": (90.0, 0.0),
            "left": (-90.0, 0.0),
            "top": (0.0, 89.0),
            "bottom": (0.0, -89.0),
        }
        if name in views:
            self.azimuth, self.elevation = views[name]
            self.pan_offset[:] = 0.0

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

    def projection_matrix(self, aspect: float) -> np.ndarray:
        if self.orthographic:
            half = self.distance * 0.5
            return np.array([
                [1.0 / (half * aspect), 0, 0, 0],
                [0, 1.0 / half, 0, 0],
                [0, 0, -2.0 / 200.0, 0],
                [0, 0, 0, 1],
            ], dtype=np.float32)
        # Perspective
        fov = math.radians(45.0)
        f = 1.0 / math.tan(fov / 2)
        near, far = 0.1, 200.0
        return np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0],
        ], dtype=np.float32)


class ViewportWidget(QOpenGLWidget if HAS_QT else object):  # type: ignore
    """moderngl-based orbit viewport with full transform support."""

    if HAS_QT:
        selection_changed = pyqtSignal()
        transform_committed = pyqtSignal(object, object, object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._scene = None
        self.camera = Camera()
        self.shading_mode = "solid"
        self.wireframe = False
        self.show_normals = False
        self.show_edges = False
        self.show_selection_outline = True
        self.gizmo_mode = "translate"
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
        self._gizmo_axis: Optional[int] = None
        self._drag_start_mouse: Optional[QPoint] = None
        self._drag_start_transform: Optional[object] = None
        self._click_threshold = 4
        self.setMinimumSize(200, 200)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @property
    def scene(self):
        return self._scene

    def set_scene(self, scene) -> None:
        self._scene = scene
        self.update()

    def toggle_wireframe(self) -> None:
        modes = ["solid", "wireframe", "solid_wire"]
        try:
            idx = modes.index(self.shading_mode)
        except ValueError:
            idx = 0
        self.shading_mode = modes[(idx + 1) % len(modes)]
        self.wireframe = self.shading_mode == "wireframe"
        self.show_edges = self.shading_mode == "solid_wire"
        self.update()

    def set_shading_mode(self, mode: str) -> None:
        if mode not in ("solid", "wireframe", "solid_wire"):
            return
        self.shading_mode = mode
        self.wireframe = mode == "wireframe"
        self.show_edges = mode == "solid_wire"
        self.update()

    def set_standard_view(self, name: str) -> None:
        self.camera.set_standard_view(name)
        self.update()

    def toggle_orthographic(self) -> None:
        self.camera.orthographic = not self.camera.orthographic
        self.update()

    def toggle_normals(self) -> None:
        self.show_normals = not self.show_normals
        self.update()

    def toggle_edges(self) -> None:
        self.show_edges = not self.show_edges
        self.update()

    def frame_all(self) -> None:
        if self._scene is None or not self._scene.objects:
            return
        points = []
        for obj in self._scene.objects:
            if not obj.visible or not obj.mesh.vertices:
                continue
            world = obj.transform.transform_points(np.array(obj.mesh.vertices, dtype=np.float32))
            points.extend(world.tolist())
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
            if obj.mesh.vertices:
                world = obj.transform.transform_points(np.array(obj.mesh.vertices, dtype=np.float32))
                points.extend(world.tolist())
        if points:
            self.camera.frame_points([np.array(p) for p in points])
            self.update()

    # ------------------------------------------------------------------
    # OpenGL
    # ------------------------------------------------------------------

    def initializeGL(self) -> None:
        if not HAS_MODERNGL:
            return
        try:
            self._ctx = moderngl.create_context()
            self._ctx.enable(moderngl.DEPTH_TEST)
            # Simple unlit shader for grid/axes/gizmos
            self._prog_unlit = self._ctx.program(
                vertex_shader="""
                    #version 330
                    in vec3 in_pos;
                    in vec3 in_color;
                    uniform mat4 mvp;
                    out vec3 v_color;
                    void main() {
                        gl_Position = mvp * vec4(in_pos, 1.0);
                        v_color = in_color;
                    }
                """,
                fragment_shader="""
                    #version 330
                    in vec3 v_color;
                    out vec4 f_color;
                    void main() {
                        f_color = vec4(v_color, 1.0);
                    }
                """,
            )
            # Lit shader for meshes
            self._prog = self._ctx.program(
                vertex_shader="""
                    #version 330
                    in vec3 in_pos;
                    in vec3 in_normal;
                    uniform mat4 mvp;
                    uniform mat4 model;
                    out vec3 v_normal;
                    out vec3 v_pos;
                    void main() {
                        gl_Position = mvp * vec4(in_pos, 1.0);
                        v_normal = mat3(model) * in_normal;
                        v_pos = in_pos;
                    }
                """,
                fragment_shader="""
                    #version 330
                    in vec3 v_normal;
                    in vec3 v_pos;
                    uniform vec3 color;
                    out vec4 f_color;
                    void main() {
                        vec3 n = normalize(v_normal);
                        vec3 light = normalize(vec3(0.5, 1.0, 0.7));
                        float diff = max(dot(n, light), 0.15);
                        f_color = vec4(color * diff, 1.0);
                    }
                """,
            )
            self._build_grid_and_axes()
        except Exception:
            self._ctx = None

    def _build_grid_and_axes(self) -> None:
        if self._ctx is None:
            return
        # Grid on XZ
        grid_lines = []
        for i in range(-10, 11):
            grid_lines.extend([i, 0, -10, 0.3, 0.3, 0.3, i, 0, 10, 0.3, 0.3, 0.3])
            grid_lines.extend([-10, 0, i, 0.3, 0.3, 0.3, 10, 0, i, 0.3, 0.3, 0.3])
        grid_arr = np.array(grid_lines, dtype=np.float32)
        self._grid_vbo = self._ctx.buffer(grid_arr.tobytes())
        self._grid_vao = self._ctx.vertex_array(
            self._prog_unlit,
            [(self._grid_vbo, "3f 3f", "in_pos", "in_color")],
        )
        # Axes
        axes = [
            # X red
            0, 0, 0, 1, 0, 0, 2, 0, 0, 1, 0, 0,
            # Y green
            0, 0, 0, 0, 1, 0, 0, 2, 0, 0, 1, 0,
            # Z blue
            0, 0, 0, 0, 0, 1, 0, 0, 2, 0, 0, 1,
        ]
        axes_arr = np.array(axes, dtype=np.float32)
        self._axes_vbo = self._ctx.buffer(axes_arr.tobytes())
        self._axes_vao = self._ctx.vertex_array(
            self._prog_unlit,
            [(self._axes_vbo, "3f 3f", "in_pos", "in_color")],
        )

    def resizeGL(self, w: int, h: int) -> None:
        if self._ctx is not None:
            self._ctx.viewport = (0, 0, w, h)

    def paintGL(self) -> None:
        if self._ctx is None:
            return
        self._ctx.clear(0.12, 0.12, 0.14, 1.0)
        aspect = self.width() / max(1, self.height())
        mvp = self.camera.projection_matrix(aspect) @ self.camera.view_matrix()
        # Grid + axes
        if self._grid_vao is not None:
            self._prog_unlit["mvp"].write(mvp.tobytes())
            self._grid_vao.render(moderngl.LINES)
        if self._axes_vao is not None:
            self._axes_vao.render(moderngl.LINES)
        # Meshes
        if self._scene is not None and self._prog is not None:
            for obj in self._scene.objects:
                if not obj.visible or not obj.mesh.vertices or not obj.mesh.faces:
                    continue
                self._draw_mesh(obj, mvp)
                # Selection outline (edge highlight)
                if self.show_selection_outline and self._scene.is_selected(obj):
                    self._draw_selection_outline(obj, mvp)
        # Gizmo for selected objects (drawn after meshes so they overlay)
        if self._scene is not None and self._prog_unlit is not None:
            selected = self._scene.selected_objects()
            if selected:
                self._draw_gizmo(selected[0], mvp)

    def _draw_mesh(self, obj, mvp) -> None:
        if self._ctx is None or self._prog is None:
            return
        verts = np.array(obj.mesh.vertices, dtype=np.float32)
        world = obj.transform.transform_points(verts)
        # Simple face normals
        faces = obj.mesh.faces
        normals = np.zeros_like(world)
        for f in faces:
            if len(f) < 3:
                continue
            p0, p1, p2 = world[f[0]], world[f[1]], world[f[2]]
            n = np.cross(p1 - p0, p2 - p0)
            n /= np.linalg.norm(n) + 1e-8
            for i in f:
                normals[i] += n
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        normals /= np.maximum(norms, 1e-8)
        data = np.hstack([world, normals]).astype(np.float32)
        vbo = self._ctx.buffer(data.tobytes())
        # Index buffer
        indices = []
        for f in faces:
            if len(f) == 3:
                indices.extend(f)
            elif len(f) == 4:
                indices.extend([f[0], f[1], f[2], f[0], f[2], f[3]])
        if not indices:
            return
        ibo = self._ctx.buffer(np.array(indices, dtype=np.uint32).tobytes())
        vao = self._ctx.vertex_array(
            self._prog,
            [(vbo, "3f 3f", "in_pos", "in_normal")],
            index_buffer=ibo,
        )
        color = [0.9, 0.5, 0.2] if self._scene and self._scene.is_selected(obj) else [0.6, 0.65, 0.7]
        model = obj.transform.matrix()
        self._prog["mvp"].write(mvp.tobytes())
        self._prog["model"].write(model.tobytes())
        self._prog["color"].value = tuple(color)
        mode = moderngl.LINES if self.wireframe else moderngl.TRIANGLES
        vao.render(mode)
        vbo.release()
        ibo.release()
        vao.release()

    def _draw_selection_outline(self, obj, mvp) -> None:
        """Draw unique edges of a selected mesh in a bright highlight color."""
        if self._ctx is None or self._prog_unlit is None:
            return
        edges = extract_unique_edges(obj.mesh.faces)
        if not edges:
            return
        verts = np.array(obj.mesh.vertices, dtype=np.float32)
        world = obj.transform.transform_points(verts)
        highlight = np.array([1.0, 0.85, 0.1], dtype=np.float32)  # bright yellow
        line_data = []
        for a, b in edges:
            line_data.extend(world[a].tolist())
            line_data.extend(highlight.tolist())
            line_data.extend(world[b].tolist())
            line_data.extend(highlight.tolist())
        if not line_data:
            return
        arr = np.array(line_data, dtype=np.float32)
        vbo = self._ctx.buffer(arr.tobytes())
        vao = self._ctx.vertex_array(
            self._prog_unlit,
            [(vbo, "3f 3f", "in_pos", "in_color")],
        )
        self._prog_unlit["mvp"].write(mvp.tobytes())
        vao.render(moderngl.LINES)
        vbo.release()
        vao.release()

    def _draw_gizmo(self, obj, mvp) -> None:
        """Draw mode-aware gizmo: arrowheads for translate, rings for rotate, boxes for scale."""
        if self._ctx is None or self._prog_unlit is None:
            return
        origin = np.array(obj.transform.location, dtype=np.float32)
        length = 1.8
        axes = self._local_axes(obj.transform, length)
        colors = [
            np.array([1.0, 0.2, 0.2], dtype=np.float32),  # X red
            np.array([0.2, 1.0, 0.2], dtype=np.float32),  # Y green
            np.array([0.2, 0.4, 1.0], dtype=np.float32),  # Z blue
        ]
        # Brighter highlight for the axis currently being dragged
        if self._gizmo_dragging and self._gizmo_axis is not None:
            colors[self._gizmo_axis] = np.array([1.0, 1.0, 0.3], dtype=np.float32)
        line_data: List[float] = []
        tri_data: List[float] = []

        mode = self.gizmo_mode or "translate"

        for i, (axis, col) in enumerate(zip(axes, colors)):
            end = origin + axis
            # Main axis line
            line_data.extend(origin.tolist())
            line_data.extend(col.tolist())
            line_data.extend(end.tolist())
            line_data.extend(col.tolist())

            if mode == "translate":
                # Arrowhead: small cone approximated by 4 triangles / lines
                tip = end
                shaft = origin + axis * 0.75
                # Perpendicular basis
                if abs(axis[1]) < 0.9:
                    side = np.cross(axis, np.array([0.0, 1.0, 0.0], dtype=np.float32))
                else:
                    side = np.cross(axis, np.array([1.0, 0.0, 0.0], dtype=np.float32))
                side /= np.linalg.norm(side) + 1e-8
                up = np.cross(axis, side)
                up /= np.linalg.norm(up) + 1e-8
                radius = 0.18
                for k in range(4):
                    ang = k * math.pi / 2
                    p = shaft + (side * math.cos(ang) + up * math.sin(ang)) * radius
                    # Lines for arrow
                    line_data.extend(tip.tolist())
                    line_data.extend(col.tolist())
                    line_data.extend(p.tolist())
                    line_data.extend(col.tolist())
                    # Optional filled triangles (simple fan)
                    next_ang = (k + 1) * math.pi / 2
                    p2 = shaft + (side * math.cos(next_ang) + up * math.sin(next_ang)) * radius
                    tri_data.extend(tip.tolist())
                    tri_data.extend(col.tolist())
                    tri_data.extend(p.tolist())
                    tri_data.extend(col.tolist())
                    tri_data.extend(p2.tolist())
                    tri_data.extend(col.tolist())

            elif mode == "rotate":
                # Ring in plane perpendicular to this axis
                if abs(axis[1]) < 0.9:
                    side = np.cross(axis, np.array([0.0, 1.0, 0.0], dtype=np.float32))
                else:
                    side = np.cross(axis, np.array([1.0, 0.0, 0.0], dtype=np.float32))
                side /= np.linalg.norm(side) + 1e-8
                up = np.cross(axis, side)
                up /= np.linalg.norm(up) + 1e-8
                radius = 1.2
                segs = 24
                for k in range(segs):
                    a1 = k * 2 * math.pi / segs
                    a2 = (k + 1) * 2 * math.pi / segs
                    p1 = origin + (side * math.cos(a1) + up * math.sin(a1)) * radius
                    p2 = origin + (side * math.cos(a2) + up * math.sin(a2)) * radius
                    line_data.extend(p1.tolist())
                    line_data.extend(col.tolist())
                    line_data.extend(p2.tolist())
                    line_data.extend(col.tolist())

            elif mode == "scale":
                # Small cube marker at end
                size = 0.15
                # Just extra cross lines for simplicity (box outline would be more verts)
                for d in (np.array([size, 0, 0]), np.array([0, size, 0]), np.array([0, 0, size])):
                    # Transform local offsets roughly by axis direction scale
                    off = d * (np.linalg.norm(axis) / length)
                    line_data.extend((end - off).tolist())
                    line_data.extend(col.tolist())
                    line_data.extend((end + off).tolist())
                    line_data.extend(col.tolist())

        # Render lines
        if line_data:
            arr = np.array(line_data, dtype=np.float32)
            vbo = self._ctx.buffer(arr.tobytes())
            vao = self._ctx.vertex_array(
                self._prog_unlit,
                [(vbo, "3f 3f", "in_pos", "in_color")],
            )
            self._prog_unlit["mvp"].write(mvp.tobytes())
            vao.render(moderngl.LINES)
            vbo.release()
            vao.release()

        # Optional filled arrowheads
        if tri_data:
            arr = np.array(tri_data, dtype=np.float32)
            vbo = self._ctx.buffer(arr.tobytes())
            vao = self._ctx.vertex_array(
                self._prog_unlit,
                [(vbo, "3f 3f", "in_pos", "in_color")],
            )
            self._prog_unlit["mvp"].write(mvp.tobytes())
            vao.render(moderngl.TRIANGLES)
            vbo.release()
            vao.release()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse = event.pos()
            self._dragging = False
            # Try gizmo first
            axis = self._hit_gizmo(event.pos().x(), event.pos().y())
            if axis is not None:
                self._gizmo_dragging = True
                self._gizmo_axis = axis
                self._drag_start_mouse = event.pos()
                selected = self._scene.selected_objects() if self._scene else []
                if selected:
                    self._drag_start_transform = Transform(
                        location=list(selected[0].transform.location),
                        rotation=list(selected[0].transform.rotation),
                        scale=list(selected[0].transform.scale),
                    )
                return
            # Otherwise prepare for possible selection or orbit
            self._drag_start_mouse = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._gizmo_dragging and self._gizmo_axis is not None:
            self._apply_gizmo_drag(event.pos())
            return
        if self._last_mouse is None:
            return
        dx = event.pos().x() - self._last_mouse.x()
        dy = event.pos().y() - self._last_mouse.y()
        if abs(dx) + abs(dy) > self._click_threshold:
            self._dragging = True
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.camera.orbit(dx * 0.4, -dy * 0.4)
            elif event.buttons() & Qt.MouseButton.MiddleButton:
                self.camera.pan(dx, dy)
            self._last_mouse = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._gizmo_dragging and self._drag_start_transform is not None and self._scene:
            selected = self._scene.selected_objects()
            if selected and HAS_QT:
                self.transform_committed.emit(selected[0], self._drag_start_transform, selected[0].transform)
        self._gizmo_dragging = False
        self._gizmo_axis = None
        if not self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._pick(event.pos())
        self._dragging = False
        self._last_mouse = None

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        self.camera.zoom(delta)
        self.update()

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
        elif key == Qt.Key.Key_F:
            self.frame_selected()
        elif key == Qt.Key.Key_Home:
            self.frame_all()
        elif key == Qt.Key.Key_1:
            self.set_standard_view("front")
        elif key == Qt.Key.Key_3:
            self.set_standard_view("right")
        elif key == Qt.Key.Key_7:
            self.set_standard_view("top")
        elif key == Qt.Key.Key_5:
            self.toggle_orthographic()
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Picking
    # ------------------------------------------------------------------

    def _screen_to_ray(self, x: int, y: int) -> Tuple[np.ndarray, np.ndarray]:
        """Convert screen coords to world ray origin + direction."""
        w, h = max(1, self.width()), max(1, self.height())
        # NDC
        ndc_x = (2.0 * x / w) - 1.0
        ndc_y = 1.0 - (2.0 * y / h)
        aspect = w / h
        proj = self.camera.projection_matrix(aspect)
        view = self.camera.view_matrix()
        inv_vp = np.linalg.inv(proj @ view)
        # Near and far points in NDC
        near = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype=np.float32)
        far = np.array([ndc_x, ndc_y, 1.0, 1.0], dtype=np.float32)
        near_w = inv_vp @ near
        far_w = inv_vp @ far
        near_w /= near_w[3]
        far_w /= far_w[3]
        origin = near_w[:3]
        direction = far_w[:3] - near_w[:3]
        direction /= np.linalg.norm(direction) + 1e-8
        return origin, direction

    def _ray_aabb(self, ray_o: np.ndarray, ray_d: np.ndarray, mn: np.ndarray, mx: np.ndarray) -> Optional[float]:
        """Slab method ray-AABB intersection. Returns t or None."""
        inv_d = 1.0 / (ray_d + 1e-12)
        t1 = (mn - ray_o) * inv_d
        t2 = (mx - ray_o) * inv_d
        tmin = np.minimum(t1, t2).max()
        tmax = np.maximum(t1, t2).min()
        if tmax < 0 or tmin > tmax:
            return None
        return float(tmin if tmin > 0 else tmax)

    def _pick(self, pos) -> None:
        if self._scene is None:
            return
        ray_o, ray_d = self._screen_to_ray(pos.x(), pos.y())
        best = None
        best_t = float("inf")
        for obj in self._scene.objects:
            if not obj.visible or not obj.mesh.vertices:
                continue
            world = obj.transform.transform_points(np.array(obj.mesh.vertices, dtype=np.float32))
            mn = world.min(axis=0) - 0.05
            mx = world.max(axis=0) + 0.05
            t = self._ray_aabb(ray_o, ray_d, mn, mx)
            if t is not None and 0 < t < best_t:
                best_t = t
                best = obj
        if best is not None:
            self._scene.select(best, clear=True)
            self.selection_changed.emit()
            self.update()
        else:
            if self._scene.selected_names():
                self._scene.clear_selection()
                self.selection_changed.emit()
                self.update()

    # ------------------------------------------------------------------
    # Gizmo helpers (pure math, headless-safe)
    # ------------------------------------------------------------------

    def _local_axes(self, transform, length: float = 1.0) -> List[np.ndarray]:
        """Return world-space offsets for local X/Y/Z axes of length."""
        mat = transform.matrix()
        axes = []
        for i in range(3):
            local = np.zeros(3, dtype=np.float32)
            local[i] = length
            world = (mat[:3, :3] @ local)
            axes.append(world)
        return axes

    def _hit_gizmo(self, x: int, y: int) -> Optional[int]:
        """Return axis index (0/1/2) if click near a gizmo axis/tip/ring, else None."""
        if self._scene is None or not self._scene.selected_objects():
            return None
        obj = self._scene.selected_objects()[0]
        origin = np.array(obj.transform.location, dtype=np.float32)
        axes = self._local_axes(obj.transform, 1.8)
        ray_o, ray_d = self._screen_to_ray(x, y)
        return hit_test_gizmo_axis(
            ray_o, ray_d, origin, axes,
            mode=self.gizmo_mode or "translate",
        )

    # Alias for older tests
    def _draw_gizmo_axes(self, obj, mvp) -> None:
        self._draw_gizmo(obj, mvp)

    def _apply_gizmo_drag(self, pos) -> None:
        if self._gizmo_axis is None or self._drag_start_transform is None or self._scene is None:
            return
        selected = self._scene.selected_objects()
        if not selected:
            return
        obj = selected[0]
        dx = pos.x() - self._drag_start_mouse.x()
        # Simple screen-space delta mapped to local axis
        scale = 0.01 * self.camera.distance
        delta = dx * scale
        start = self._drag_start_transform
        if self.gizmo_mode == "translate":
            axes = self._local_axes(start, 1.0)
            axis_dir = axes[self._gizmo_axis]
            axis_dir /= np.linalg.norm(axis_dir) + 1e-8
            obj.transform.location = (
                np.array(start.location, dtype=np.float32) + axis_dir * delta
            ).tolist()
        elif self.gizmo_mode == "rotate":
            obj.transform.rotation = list(start.rotation)
            obj.transform.rotation[self._gizmo_axis] = start.rotation[self._gizmo_axis] + delta * 0.5
        elif self.gizmo_mode == "scale":
            obj.transform.scale = list(start.scale)
            obj.transform.scale[self._gizmo_axis] = max(0.01, start.scale[self._gizmo_axis] + delta * 0.1)
        self.update()
