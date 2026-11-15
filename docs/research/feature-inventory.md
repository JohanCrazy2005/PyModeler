# PyModeler Feature Inventory (Prioritized) — CAD / CAM Focus

Synthesized from research on Fusion 360 / Autodesk Fusion, Onshape, and Mozaik, aligned with the parametric CAD + design-to-manufacture goal.

**Goal**: A user can create parametric parts from constrained sketches and features, build simple assemblies, generate cut lists / basic manufacturing outputs, and export usable geometry in a workflow familiar to Fusion 360 / Onshape users, with practical manufacturing helpers inspired by Mozaik.

## Priority Tiers

### P0 – Foundation (largely complete)
- [x] Robust Mesh data model (legacy utility) + JSON Schema
- [x] Scene graph basics + JSON Schema
- [x] Undo/Redo command stack
- [x] Basic PyQt6 application shell
- [x] Cross-platform dependencies + CI skeleton
- [x] Automated tests for core data + smoke test
- [ ] Ensure remaining foundation modules are complete and all tests pass cleanly

### P1 – Parametric Core: Sketch + Features (next major phase)
- Sketch schema + data model (entities: line, circle, arc, rectangle, etc.; constraints; dimensions)
- Basic 2D sketch editor in UI (create on plane, draw, constrain, dimension)
- User Parameters / variables system (named values that drive dimensions)
- Extrude feature (from sketch profile to solid) with parameters (distance, direction, operation type)
- Feature history / timeline data model + simple UI (feature tree)
- Revolve feature
- Fully constrained sketch indicators and validation

### P2 – Parts, Assemblies & Manufacturing Helpers
- Multi-feature Part model (solid body from feature history)
- Simple Assembly + mates / constraints
- Cut list / part list generation (Mozaik-inspired: materials, sizes, quantities)
- Basic BOM
- Material / stock definitions
- Dimensioned drawing / export stubs
- Configurations (independent inputs driving parameters and suppressions)

### P3 – Viewport, Interaction & Polish
- Real OpenGL / moderngl viewport improvements (already started)
- Camera controls, selection, feature highlighting
- Transform tools that respect parametric intent where possible
- Snapping in sketch and 3D

### P4 – Advanced CAD + Path to CAM
- Fillet / Chamfer / Shell / Hole features
- Sheet metal / panel basics
- Simple nesting concepts and material optimization
- Early toolpath / G-code generation stubs
- Import/Export improvements (STEP later if geometry kernel allows)
- Joinery rules / automatic machining concepts (furniture-focused)

## Comparison Notes
- **Fusion 360**: Excellent reference for sketch constraints, dimensions, parameters, timeline, and mixed parametric/direct workflows.
- **Onshape**: Strong model for Part Studio + feature list, clean multi-part handling, and modern independent configuration inputs.
- **Mozaik**: Practical manufacturing focus — automatic cut lists, nesting, joinery rules, BOMs, and CNC outputs. Valuable for design-to-manufacture helpers even if the core is general parametric CAD.

## Recommended Immediate Build Order
1. Complete research documentation (this inventory + detailed notes).
2. Finish any missing foundation pieces and keep tests green.
3. Implement Sketch JSON Schema + core data model.
4. Add basic Parameter system.
5. Implement simple Extrude feature that produces a solid (initially via mesh or simple geometry).
6. Add feature history data model and timeline UI stub.
7. Begin 2D sketch editor UI.
8. Add cut-list generation stub once parts exist.

This inventory will be refined as implementation proceeds and more focused research is done on specific areas (e.g., constraint solver, B-Rep kernel options).
