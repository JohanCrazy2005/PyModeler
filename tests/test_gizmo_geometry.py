"""Pure math tests for gizmo geometry helpers (no Qt / GL required)."""

import math
import numpy as np

from pymodeler.render.viewport import generate_ring_points, generate_arrow_base_points, extract_unique_edges


def test_extract_unique_edges_cube():
    # Cube faces (quads)
    faces = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [0, 1, 5, 4],
        [2, 3, 7, 6],
        [0, 3, 7, 4],
        [1, 2, 6, 5],
    ]
    edges = extract_unique_edges(faces)
    assert len(edges) == 12


def test_generate_ring_points():
    center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    normal = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    pts = generate_ring_points(center, normal, radius=2.0, segments=8)
    assert len(pts) == 8
    for p in pts:
        assert abs(np.linalg.norm(p) - 2.0) < 1e-5
        assert abs(p[1]) < 1e-5  # in XZ plane


def test_generate_arrow_base_points():
    tip = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    shaft = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    pts = generate_arrow_base_points(tip, shaft, radius=0.2, segments=4)
    assert len(pts) == 4
    for p in pts:
        # Should be near the shaft end, offset perpendicular
        assert np.linalg.norm(p - tip) > 0.1
        assert abs(np.dot(p - tip, shaft)) < 0.5  # roughly perpendicular-ish
