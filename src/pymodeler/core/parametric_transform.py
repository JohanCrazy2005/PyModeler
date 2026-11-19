"""Helpers that apply transform intent back into parametric data.

When a user moves a generated body with the gizmo, we prefer to update
the driving sketch (plane origin + free points) so the change survives
recompute, instead of leaving only a free mesh transform.
"""

from __future__ import annotations

from typing import Optional

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
