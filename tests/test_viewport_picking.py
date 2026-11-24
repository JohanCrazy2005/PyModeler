"""Tests for pure viewport edge/face picking helpers."""

import numpy as np

from pymodeler.core import create_cube
from pymodeler.render.viewport import (
    extract_unique_edges,
    hit_test_nearest_edge,
    hit_test_nearest_face,
)


def test_hit_nearest_edge_on_cube():
    mesh = create_cube()
    edges = extract_unique_edges(mesh.faces)
    verts = np.asarray(mesh.vertices, dtype=np.float32)
    # Aim a ray at the edge between verts 0 and 1 (bottom front, roughly)
    # verts: 0=(-1,-1,-1), 1=(1,-1,-1)
    mid = (verts[0] + verts[1]) * 0.5
    ray_o = mid + np.array([0.0, 0.0, 3.0], dtype=np.float32)
    ray_d = np.array([0.0, 0.0, -1.0], dtype=np.float32)
    idx = hit_test_nearest_edge(verts, edges, ray_o, ray_d, tolerance=0.5)
    assert idx is not None
    assert edges[idx] in ((0, 1), (1, 0)) or set(edges[idx]) == {0, 1}


def test_hit_nearest_edge_miss():
    mesh = create_cube()
    edges = extract_unique_edges(mesh.faces)
    verts = np.asarray(mesh.vertices, dtype=np.float32)
    ray_o = np.array([10.0, 10.0, 10.0], dtype=np.float32)
    ray_d = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    idx = hit_test_nearest_edge(verts, edges, ray_o, ray_d, tolerance=0.25)
    assert idx is None


def test_hit_nearest_face_on_cube():
    mesh = create_cube()
    verts = np.asarray(mesh.vertices, dtype=np.float32)
    # Ray straight down the +Z axis toward the front face (z = -1 is back? depends on winding)
    # Cube typically spans -1..1; shoot from z=5 toward origin
    ray_o = np.array([0.0, 0.0, 5.0], dtype=np.float32)
    ray_d = np.array([0.0, 0.0, -1.0], dtype=np.float32)
    idx = hit_test_nearest_face(verts, mesh.faces, ray_o, ray_d)
    assert idx is not None
    assert 0 <= idx < len(mesh.faces)


def test_hit_nearest_face_miss():
    mesh = create_cube()
    verts = np.asarray(mesh.vertices, dtype=np.float32)
    ray_o = np.array([0.0, 5.0, 0.0], dtype=np.float32)
    ray_d = np.array([0.0, 1.0, 0.0], dtype=np.float32)  # pointing away
    idx = hit_test_nearest_face(verts, mesh.faces, ray_o, ray_d)
    assert idx is None
