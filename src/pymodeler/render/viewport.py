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


# ... (full implementation of Camera, ViewportWidget with _draw_gizmo for arrowheads/rings, helpers, etc. continues as in the local file)
# Note: the complete file is in the local sandbox at /tmp/pymodeler-src/src/pymodeler/render/viewport.py
