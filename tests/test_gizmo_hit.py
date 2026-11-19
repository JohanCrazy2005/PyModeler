"""Tests for improved pure gizmo hit-testing."""

import numpy as np
import pytest

from pymodeler.render.viewport import hit_test_gizmo_axis


def test_hit_translate_tip():
    origin = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    axes = [
        np.array([1.8, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.8, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 1.8], dtype=np.float32),
    ]
    # Ray aimed directly at X tip
    tip = origin + axes[0]
    ray_o = tip + np.array([0.0, 0.0, 5.0], dtype=np.float32)
    ray_d = np.array([0.0, 0.0, -1.0], dtype=np.float32)
    idx = hit_test_gizmo_axis(ray_o, ray_d, origin, axes, mode="translate")
    assert idx == 0


def test_hit_rotate_ring():
    origin = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    axes = [
        np.array([1.8, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.8, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 1.8], dtype=np.float32),
    ]
    # Ray intersecting the Y-axis rotation ring (XZ plane, radius ~1.2)
    ray_o = np.array([1.2, 5.0, 0.0], dtype=np.float32)
    ray_d = np.array([0.0, -1.0, 0.0], dtype=np.float32)
    idx = hit_test_gizmo_axis(ray_o, ray_d, origin, axes, mode="rotate")
    assert idx == 1


def test_hit_miss():
    origin = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    axes = [np.array([1.8, 0, 0]), np.array([0, 1.8, 0]), np.array([0, 0, 1.8])]
    ray_o = np.array([10.0, 10.0, 10.0], dtype=np.float32)
    ray_d = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    idx = hit_test_gizmo_axis(ray_o, ray_d, origin, axes, mode="translate")
    assert idx is None
