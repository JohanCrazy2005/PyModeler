# Chamfer Feature

Research notes for the Chamfer (edge bevel) feature in Fusion 360, Onshape, and manufacturing-oriented tools.

## Fusion 360

- Dedicated **Chamfer** tool under Design > Solid > Modify > Chamfer.
- Selection: edges, faces (all edges of face), or features.
- Types:
  - **Equal Distance**: same distance on both adjacent faces.
  - **Two Distance**: different distances on each face.
  - **Distance And Angle**: one distance + angle.
- Corner types: Chamfer, Miter, Blend.
- Supports multiple selection sets with independent settings.
- Parametric; distances/angles can be driven by parameters.
- Tangent chain option.

Sources: Autodesk Fusion Help – Create a chamfer, Chamfer reference.

## Onshape

- Chamfer feature for beveling edges or faces.
- Measurement types: Offset (distance from original edge) or Tangent (from tangent intersection).
- Types: Equal distance, Two distances, Distance and angle.
- Flip option for asymmetric cases.
- Tangent propagation by default.
- Dedicated chamfer dimension tool for drawings.

Sources: Onshape Help / Tech Tips – Understanding the Chamfer Feature Tool.

## Manufacturing relevance

- Chamfers break sharp edges for safety, improve part fit, reduce stress concentrations at corners, and aid tool entry/exit in CNC.
- Common on machined parts, sheet-metal edges, and castings.
- Parametric control enables consistent callouts and future CAM awareness.

## Implications for PyModeler

Current mesh-based approach:

1. Schema for ChamferFeature with distance (numeric or parameter), optional edge selection (list of edge indices or identifiers), operation="modify". Start with equal-distance mode.
2. Stub implementation: store the intent; generate a placeholder mesh (short cone) or note that full edge bevel on mesh is deferred (requires robust B-rep or advanced mesh bevel).
3. Integrate into FeatureHistory so it appears in the timeline and can be suppressed/rollback.
4. Later: basic mesh bevel approximation for selected edges, support for two-distance / distance-angle, or wait for geometry kernel.

This continues Phase 4 advanced features after Fillet stub.

## 2026-11-21 update
Basic mesh bevel approximation improved:
- Offsets now computed from average adjacent-face normals + true perpendicular direction.
- Corner fans added where multiple beveled edges meet at a vertex.
- Optional lightweight cleanup (merge near-coincident verts, drop degenerate faces).
Still a mesh approximation; full rolling-ball / B-rep quality deferred until a geometry kernel is available.
