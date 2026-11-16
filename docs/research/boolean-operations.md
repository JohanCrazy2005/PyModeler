# Boolean Operations (Join / Cut / Intersect)

Research note for implementing Boolean operations on generated meshes in PyModeler, aligned with Fusion 360 and Onshape.

## Fusion 360
- Command: **Combine** (Design > Solid > Modify > Combine).
- Operations:
  - **Join**: union of target + tool bodies into a single body.
  - **Cut**: subtract tool volume from target.
  - **Intersect**: keep only the overlapping volume.
- Target body is modified; tool bodies can optionally be kept.
- Also available as the `operation` option on Extrude / Revolve / etc. (New Body, Join, Cut, Intersect).
- Requires solid (watertight) bodies. Near-coincident faces or tiny gaps can cause failures; Fusion sometimes falls back to a mesh-assisted path.

## Onshape
- Dedicated **Boolean** feature in Part Studio: Union / Subtract / Intersect.
- Same operations appear as options on Extrude, Revolve, Sweep, Loft, etc. (New / Add / Remove / Intersect) with a merge scope.
- Subtract supports an optional offset for clearance.
- Parts must intersect; Keep tools is available on all three operations.

## Mozaik / manufacturing context
- Boolean-style cuts are the basis for joinery, pockets, and hole patterns that feed cut lists and CNC outputs. Exact B-Rep is ideal; mesh Booleans are an acceptable early approximation for visualization and simple manufacturing previews.

## Implementation approach for PyModeler
- Schema already stores `operation: "new" | "join" | "cut" | "intersect"` on Extrude and Revolve.
- Currently only `"new"` is realized (each feature produces an independent mesh).
- Next step: during FeatureHistory recompute, accumulate a current body mesh and apply the requested Boolean when operation ≠ "new".
- Engine: use `trimesh` + optional `manifold3d` (cross-platform, pip-installable, pure Python bindings to a robust mesh Boolean library). Fallback: simple vertex/face concatenation for Join when the engine is unavailable; clear error for Cut/Intersect.
- Limitations of mesh Booleans: not as robust as B-Rep kernels (CadQuery / OCP); coplanar faces and non-manifold input can fail. Sufficient for early parametric preview and manufacturing helpers.

## References
- Autodesk Fusion Combine help
- Onshape Boolean / Extrude Boolean options
- trimesh.boolean (manifold3d backend)
