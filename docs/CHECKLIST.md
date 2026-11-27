# PyModeler Development Checklist

Living checklist. Mark [x] when complete and tested.

## Phase 0 – Foundation
- [x] Repo structure, schemas/, src/, tests/, docs/
- [x] JSON Schema validation infrastructure
- [x] Basic Sketch / Point / Line models
- [x] Parameter store

## Phase 1 – Sketching + Parametric Features
- [x] Sketch entities (point, line, circle, arc, rectangle)
- [x] Constraints + dimensions (schema + basic solver stub)
- [x] Extrude / Revolve features + mesh generation
- [x] FeatureHistory + recompute
- [x] Sketch canvas tools (select, draw modes, snap, multi-select, box select)
- [x] Canvas constraint + dimension badges

## Phase 2 – Parts, Assemblies, Manufacturing Helpers
- [x] Part model + materials / stock
- [x] Cut list / BOM
- [x] Assembly mates
- [x] Configurations
- [x] DXF I/O (ezdxf) including dimensions

## Phase 3 – Viewport + Direct Modeling
- [x] Viewport essentials (axes, views, shading, orthographic)
- [x] Selection + outline highlight
- [x] Gizmo (translate/rotate/scale) with parametric intent
- [x] Viewport edge/face picking

## Phase 4 – Advanced Features + Polish
- [x] Hole / Fillet / Chamfer / Shell features (stubs → basic mesh)
- [x] Sheet-metal rule + bend allowance
- [x] Rectangular nesting + toolpath / G-code stubs
- [x] Canvas badge polish: visibility toggle, hover highlight, double-click dimension edit, related-entity selection on badge click
- [x] Viewport picking further polish (multi-select Shift, box select, select-other ~, mode keys O/E/T, green entity highlight, multi-hit helpers)
- [x] Improve shell offset quality (true constant-thickness / openings via Boolean)
- [x] Manufacturing drawing polish (dimension groups UI, handle association)
- [ ] Canvas badges further polish: proper SVG glyphs, in-place edit, drag badges
- [ ] Basic STEP import/export (when geometry kernel allows)

## Phase 5 – Later
- [ ] Full constraint solver
- [ ] Sheet metal unfold
- [ ] CAM toolpaths beyond stubs
- [ ] Assemblies with more mate types

Last updated: 2026-11-27 (manufacturing drawing polish – ordinate groups UI)
