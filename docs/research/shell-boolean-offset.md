# Optional Boolean-based Shell Offset

Research note for improving shell quality when a robust Boolean engine is available.

## Motivation

- Fusion 360 / Onshape shell features produce clean, manifold hollow solids (outer body minus inner offset body).
- The existing mesh wall-stitching approximation in `ShellFeature.apply_to_mesh` works for simple cases but can produce non-manifold or self-intersecting results on more complex geometry.
- When `trimesh` + optional `manifold3d` is present, a Boolean difference of an inward-offset solid yields higher-quality topology.

## Approach used

- For closed shells (`faces` empty) with `direction="inside"`:
  1. Compute the same mitered inward vertex offset already used by the wall path.
  2. Build an inner solid from those vertices + original faces.
  3. Call `mesh_boolean(base, inner, "cut")`.
  4. On success, return the Boolean result (proper hollow solid).
- Any failure (engine missing, non-manifold inputs, empty result, etc.) silently falls back to the existing wall-stitching method.
- Openings and non-inside directions continue to use the wall method (Boolean with openings is more involved).

## Update 2026-11-27 – Mitered vertex-normal offset

- Replaced the crude centroid-scale inward offset with a **mitered vertex-normal offset**.
- For each vertex the average of adjacent face normals is computed; the offset distance is scaled by `max(1 / dot(avg_n, face_n))` (clamped) so that each adjacent face moves approximately by the requested thickness.
- This yields near-constant wall thickness on boxes, prisms, and other polyhedra with sharp corners (verified on the unit cube: inner extent = outer extent − thickness).
- Both the Boolean path (`_boolean_shell`) and the wall-stitching fallback (`_wall_stitch_shell`) now use the mitered offset.
- Openings continue to use the wall-stitch path (Boolean with openings is more involved and still deferred).
- `create_cube` face winding was corrected so all normals point outward (required for reliable normal-based offsets).

## Remaining limitations

- High-curvature or non-convex shapes still need a proper SDF / voxel / B-Rep offset kernel for guaranteed constant thickness.
- Openings are not yet produced by the Boolean path.

## References

- Existing `boolean.py` + `repair_mesh`
- Fusion 360 Shell / Onshape Shell documentation
- manifold3d Boolean guarantees
