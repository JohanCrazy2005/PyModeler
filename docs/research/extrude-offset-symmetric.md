# Extrude Start Offset and Symmetric Behavior Research

**Sources**: Fusion 360 Help (Extrude solid), Onshape Extrude documentation, community tutorials and FeatureScript discussions.

**Date**: 2026-11-15

## Fusion 360

- **Start** options: Profile Plane (default), Offset (numeric distance from profile plane), Object (from selected face/plane).
- **Direction**:
  - One Side
  - Two Sides (independent distances)
  - Symmetric with Measurement: Half Length (distance each side) or Whole Length (distance is total, half each side).
- Offset is parametric and can be driven by parameters.
- Positive offset typically moves the start in the positive extrusion direction.

## Onshape

- **Starting Offset**: Optional; Blind (numeric distance) or Entity (from parallel face/part/mate connector). Can flip direction.
- **Symmetric**: Available for Blind / Through all; depth is the *total* depth (half each side).
- Second end position for asymmetric two-sided extrudes.
- Offsets reduce the number of sketches needed for features that do not start on the sketch plane.

## Practical Notes for PyModeler

Current implementation already supports `symmetric` (treating `distance` as total length, extruding ±distance/2).

Next increment:
- Add `start_offset` (numeric or parameter/expression string) that shifts the start of the extrusion along the direction vector.
- For non-symmetric: start at `offset`, end at `offset + distance`.
- For symmetric: center the extrusion on `offset` (from `offset - half` to `offset + half`).
- Keep JSON Schema as source of truth; validate on load/save.
- Mesh generation must apply the offset to both polygon and circle profiles.

This keeps the feature parametric and aligned with Fusion/Onshape behavior while remaining simple for the current mesh-based solid generation.
