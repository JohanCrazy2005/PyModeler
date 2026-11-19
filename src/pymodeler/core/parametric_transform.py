"""Helpers that apply transform intent back into parametric data.

When a user moves a generated body with the gizmo, we prefer to update
the driving sketch (plane origin + free points, scale, plane axes) so the
change survives recompute, instead of leaving only a free mesh transform.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np

from .sketch import Sketch


def apply_translation_to_sketch(
    sketch: Sketch,
    dx: float,
    dy: float,
    dz: float = 0.0,
) -> None:
    """Offset a sketch's plane origin and all point entities by the given delta.

    This keeps the parametric definition in sync with a free translation
    applied to the resulting solid. Points are offset in the sketch's 2D
    plane (assuming the dominant axes for now; full plane projection is
    future work).
    """
    # Move plane origin
    origin = sketch.plane.get("origin", [0.0, 0.0, 0.0])
    origin = [float(origin[0]) + dx, float(origin[1]) + dy, float(origin[2]) + dz]
    sketch.plane["origin"] = origin

    # Offset free points (simple 2D for sketches that live in XY)
    for ent in sketch.entities:
        if ent.get("type") == "point" and not ent.get("fixed", False):
            ent["x"] = float(ent.get("x", 0.0)) + dx
            ent["y"] = float(ent.get("y", 0.0)) + dy

    sketch.validate()


def apply_translation_to_part_sketches(part, dx: float, dy: float, dz: float = 0.0) -> None:
    """Apply a translation intent to every sketch belonging to a Part."""
    for sk in part.sketches.values():
        apply_translation_to_sketch(sk, dx, dy, dz)


def apply_scale_to_sketch(
    sketch: Sketch,
    sx: float,
    sy: float,
    sz: float = 1.0,
) -> None:
    """Scale free points and radii relative to the sketch 2D origin.

    Also proportionally updates numeric driving dimensions (length, radius).
    Assumes the sketch lives primarily in its local XY for the scale factors
    (consistent with the simple translation path).
    """
    for ent in sketch.entities:
        etype = ent.get("type")
        if etype == "point" and not ent.get("fixed", False):
            ent["x"] = float(ent.get("x", 0.0)) * sx
            ent["y"] = float(ent.get("y", 0.0)) * sy
        elif etype in ("circle", "arc"):
            scale_r = (abs(sx) + abs(sy)) / 2.0
            ent["radius"] = float(ent.get("radius", 1.0)) * max(scale_r, 1e-6)

    # Update numeric dimensions
    avg_scale = (abs(sx) + abs(sy)) / 2.0
    for dim in sketch.dimensions:
        val = dim.get("value")
        if isinstance(val, (int, float)) and not dim.get("driven", False):
            dtype = dim.get("type")
            if dtype in ("length", "distance", "radius", "diameter"):
                dim["value"] = float(val) * avg_scale

    sketch.validate()


def apply_scale_to_part_sketches(part, sx: float, sy: float, sz: float = 1.0) -> None:
    """Apply a scale intent to every sketch belonging to a Part."""
    for sk in part.sketches.values():
        apply_scale_to_sketch(sk, sx, sy, sz)


def _euler_xyz_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    """Rotation matrix for Euler XYZ (radians)."""
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return np.array(
        [
            [cy * cz, -cy * sz, sy],
            [sx * sy * cz + cx * sz, -sx * sy * sz + cx * cz, -sx * cy],
            [-cx * sy * cz + sx * sz, cx * sy * sz + sx * cz, cx * cy],
        ],
        dtype=np.float64,
    )


def apply_rotation_to_sketch_plane(
    sketch: Sketch,
    dax: float,
    day: float,
    daz: float,
) -> None:
    """Rotate the sketch plane axes (and origin if non-zero) by an Euler delta.

    The 2D entity coordinates stay unchanged; the plane reorientation carries
    the parametric intent of a free rotation.
    """
    rot = _euler_xyz_matrix(dax, day, daz)
    x_axis = np.array(sketch.plane.get("x_axis", [1.0, 0.0, 0.0]), dtype=np.float64)
    y_axis = np.array(sketch.plane.get("y_axis", [0.0, 1.0, 0.0]), dtype=np.float64)
    origin = np.array(sketch.plane.get("origin", [0.0, 0.0, 0.0]), dtype=np.float64)

    sketch.plane["x_axis"] = (rot @ x_axis).tolist()
    sketch.plane["y_axis"] = (rot @ y_axis).tolist()
    if float(np.linalg.norm(origin)) > 1e-8:
        sketch.plane["origin"] = (rot @ origin).tolist()

    sketch.validate()


def apply_rotation_to_part_sketch_planes(
    part,
    dax: float,
    day: float,
    daz: float,
) -> None:
    """Apply a rotation intent to the plane of every sketch in a Part."""
    for sk in part.sketches.values():
        apply_rotation_to_sketch_plane(sk, dax, day, daz)
