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

## Limitations

- True constant-thickness offset on non-convex or high-curvature shapes still needs a better offset kernel (voxel/SDF or B-Rep).
- Openings are not yet handled by the Boolean path.
- Requires a working Boolean engine for the quality improvement; otherwise behavior is unchanged.

## References

- Existing `boolean.py` + `repair_mesh`
- Fusion 360 Shell / Onshape Shell documentation
- manifold3d Boolean guarantees
