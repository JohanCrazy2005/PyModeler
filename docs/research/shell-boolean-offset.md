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

## Update 2026-11-27 – Constant-thickness miter offset

Replaced centroid scaling with miter-corrected vertex-normal offset:

1. Repair mesh (fix winding/normals via trimesh).
2. Per-vertex scale = thickness / max(|vn · fn|) over adjacent faces (clamped).
3. Boolean:
   - inside: original − inward_offset
   - outside: outward_offset − original
   - both: outward_(t/2) − inward_(t/2)
4. Openings: after Boolean, drop result faces whose centroid/normal match selected original faces.

Validated volumes on `create_cube(10)`:
- inside t=1 → 488 (= 10³−8³)
- outside t=1 → 728 (= 12³−10³)
- both t=2 → 1216 (= 12³−8³)

Wall-stitch fallback uses the same miter normals for consistent thickness when Boolean is unavailable.
