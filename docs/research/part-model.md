# Multi-Feature Part Model

Research notes for the next Phase 2 item: a Part that aggregates sketches, parameters, and a FeatureHistory into a single recomputable solid body.

## Fusion 360 / Autodesk Fusion
- A *Component* (or Body inside a component) is built from an ordered feature timeline.
- Sketches and user parameters live in the design; features reference them.
- Recompute walks the timeline, producing one or more solid/surface bodies.
- Bodies can be combined via Boolean features (Join, Cut, Intersect).

## Onshape
- **Part Studio** is the container: one ordered feature list can produce *multiple independent parts*.
- Sketches, variables, and features are shared inside the studio.
- Each resulting solid is a distinct Part that can be inserted into Assemblies.
- Rollback marker suppresses features after a point (same concept we already have).

## Mozaik / manufacturing angle
- A Part should carry material/stock info so cut-list generation is straightforward later.
- Simple metadata (thickness, grain direction, edge banding) is useful even if not fully used yet.

## PyModeler design decisions (this increment)
- `Part` owns:
  - `sketches: dict[str, Sketch]`
  - `parameters: ParameterStore`
  - `feature_history: FeatureHistory`
  - optional `material` string / dict
  - cached or on-demand body `Mesh`
- `recompute()` walks the active features (respecting rollback) and produces a single body mesh.
  - For now: sequential Join of generated meshes (using existing `mesh_boolean` with fallback concatenation).
  - Later: proper solid kernel or per-feature operation type (new/join/cut/intersect).
- JSON Schema driven; round-trip via `to_dict` / `from_dict`.
- Integration point: MainWindow can hold one or more Parts; FeatureTree already displays FeatureHistory.

## Next after this
- UI: “New Part” + property panel for Part-level material.
- Cut-list stub that walks Parts and emits size/quantity/material.
- Assembly container that references Parts.

Last updated: 2026-11-17
