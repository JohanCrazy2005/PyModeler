# Manifold Repair for Boolean Operations

Research and implementation note for improving robustness of mesh Booleans in PyModeler when a Boolean engine (trimesh + optional manifold3d) is available.

## Why repair matters

- Fusion 360 and Onshape expect solid (watertight, manifold) bodies for Combine / Boolean features. Near-coincident faces, tiny gaps, inverted normals, or duplicate vertices cause failures or thin shards.
- Mesh Boolean libraries (manifold3d, trimesh) are more reliable when inputs are cleaned.
- Manifold3d itself provides a `Merge` helper for slightly non-manifold meshes; broader repair is usually done upstream.

## Common repair steps (from trimesh / industry practice)

1. Merge coincident or near-coincident vertices.
2. Remove duplicate and degenerate (zero-area) faces.
3. Remove unreferenced vertices.
4. Fix winding consistency and face normals.
5. Fill simple (triangle or quad) boundary holes.

These steps are cheap and preserve the intended solid for typical CAD-generated meshes.

## Implementation in PyModeler

- Added `repair_mesh()` in `src/pymodeler/core/boolean.py`.
- `mesh_boolean()` now calls it on both operands before attempting the engine Boolean (when trimesh is present).
- On failure or missing trimesh the original mesh is returned unchanged.
- Fallback concatenation for Join remains available when the engine fails.

## Limitations

- Full voxel/SDF remeshing or advanced hole filling (non-convex, large openings) is out of scope.
- True B-Rep kernels (CadQuery / OCP) will eventually supersede mesh Booleans for production quality.
- Optional `manifold3d` is recommended (`pip install manifold3d`) for guaranteed-manifold results.

## References

- trimesh.repair documentation
- Manifold library wiki (elalish/manifold)
- Fusion 360 Combine / Onshape Boolean help (solid body requirements)
