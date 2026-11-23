# Development Checklist

Status legend: [ ] Todo  [~] In progress  [x] Done  [-] Deferred

## Phase 0 – Foundation
- [x] Create public GitHub repository
- [x] Define GOAL, PLAN, CHECKLIST, NEXT_STEPS
- [x] Project skeleton with src/, schemas/, tests/, docs/, output/
- [x] JSON Schema for core Mesh data model (legacy / utility)
- [x] JSON Schema for Scene
- [x] Basic PyQt6 application window
- [x] Cross-platform dependency list
- [x] Automated tests for core data + smoke test
- [x] Continuous integration skeleton (GitHub Actions)
- [x] Ensure all core source modules are complete and tested on main

## Research & Planning (Mandatory)
- [x] Create `docs/research/` folder
- [x] Research notes: Fusion 360 parametric modeling, sketches, features, assemblies, CAM overview
- [x] Research notes: Onshape Part Studios, feature history, configurations, collaboration model
- [x] Research notes: Mozaik cut lists, nesting, joinery, hardware, G-code / manufacturing outputs
- [x] Prioritized feature inventory document aligned with Fusion/Onshape/Mozaik goal
- [x] Refine PLAN.md and this CHECKLIST with concrete next implementation steps

## Phase 1 – Parametric Core (Sketch + Features)
- [x] Sketch schema + data model (entities, constraints, dimensions)
- [x] User Parameters / variables system
- [x] Basic 2D sketch editor in UI
- [x] Extrude feature (from sketch to solid) with parameters
- [x] Feature history / timeline data model + simple recompute
- [x] Revolve feature
- [x] Fully constrained sketch validation (DOF analysis stub + entity status + canvas coloring)
- [x] Better closed-profile extraction (polygons, circles, basic arcs) for features
- [x] Extrude start offset and improved symmetric (schema + mesh generation)
- [x] Basic mesh Boolean helpers (join/cut/intersect) + FeatureHistory integration (optional manifold3d)
- [x] Rollback marker and basic feature reordering (data model + recompute)
- [x] Feature tree UI: set rollback marker via context menu + visual suppressed state
- [x] Visual 2D canvas for sketching (mouse drawing, basic snapping, preview)
- [x] Canvas selection of entities + drag points to update coordinates
- [x] Rectangle and Arc tools on the visual canvas
- [x] Constraint visual feedback / badges on canvas (colored markers + tooltips)
- [x] Real solid-of-revolution mesh for Revolve (profile points, partial angles, Y-axis)
- [x] Lightweight 2D constraint solver stub (scipy least_squares for horizontal/vertical/equal/coincident/parallel/perpendicular + driving dimensions length/distance/radius/diameter/angle + free radii + **parameter name evaluation for dimension values** + **full arithmetic expression evaluation for dimension values (e.g. "width * 2 + offset")** + **trig / unit-aware functions (sin/cos in degrees, sqrt, pi, in_to_mm, ...)**)

## Phase 2 – Parts, Assemblies & Manufacturing Helpers
- [x] Multi-feature Part model
- [x] Light UI integration of Parts (MainWindow + FeatureTree + cut-list display)
- [x] Multi-part switching UI (parts list, switch current_part, feature tree updates)
- [x] Simple Assembly data model (instances + transforms; mates later)
- [x] Assembly mates / constraints (rigid/fastened schema + basic solver)
- [x] Cut list / part list generation (Mozaik-inspired) — stub implemented
- [x] Cut-list enhancements: group by material/thickness + CSV export
- [x] Basic BOM
- [x] Dimensioned drawing / export stubs (DXF via ezdxf)
- [x] Material / stock definitions
- [x] UI exposure of mates, BOM, and grouped cut-list / CSV export
- [x] Configurations (independent inputs)
- [x] Visualize assembly instances in viewport (transforms)
- [x] UI panel for selecting and applying configuration values (list / numeric / boolean)

## Phase 3 – Viewport, Interaction & Polish
- [x] Real OpenGL / moderngl viewport improvements (orbit, pan, zoom, grid, RGB axes, shading modes, standard views, ortho)
- [x] Camera controls, selection, feature highlighting (selection clear-on-miss + keyboard frame/views + full transform framing/picking + paint path)
- [x] Full object transform (scale + rotation + location) applied to world vertices for framing, picking, and (when GL restored) drawing
- [x] Selection outline / edge highlight overlay in the viewport
- [x] Transform tools that respect parametric intent where possible (gizmo visuals + translate/scale/rotate drive sketches/planes + recompute; **constraint-aware: locked/coincident points preserved**)
- [x] Gizmo polish: better hit-testing (tips/rings) + drag visual feedback

## Phase 4 – Advanced CAD + Path to CAM
- [~] Fillet / Chamfer / Shell / Hole features (Hole through-all; Fillet/Chamfer basic mesh bevel via Mesh.bevel_edges + apply_to_mesh; Chamfer equal/two-distance/distance-angle modes; Hole direction vector orientation + property panel UI exposure; **Fillet/Chamfer/Shell property panel UI exposure (radius, mode, thickness, direction)**; Shell feature: schema + history + basic mesh shell approximation (normal offset + walls, optional openings) + **corner mitering via scale-adjusted vertex normals**; **UI edges/faces selection via property panel text field**; profile arcs + nested holes; true solid-of-revolution for Revolve; Extrude subtracts nested hole profiles; **Improved bevel: normal-based offsets, corner fans, optional cleanup**)
- [~] Sheet metal / panel basics (**SheetMetalRule schema + store + bend_allowance helper + research notes done**; flange / flat-pattern / nesting still todo)
- [x] Simple nesting concepts (NestingJob schema + shelf packer + from-cutlist helper + research + **multi-sheet-size selection**)
- [x] Early toolpath / G-code generation stubs (ToolpathJob schema + rectangular pocket & contour G-code generator + research)
- [x] Toolpath zig-zag pocket strategy (schema + generator + tests)
- [x] Toolpath linear lead-in / lead-out (optional lengths, schema + generator + tests)
- [x] Toolpath spiral pocket strategy (schema + generator + tests)
- [ ] Import/Export improvements (DXF via ezdxf; STEP later if geometry kernel allows)
- [ ] Joinery rules / automatic machining concepts

## Ongoing
- [ ] Keep all data structures under JSON Schemas
- [ ] Tests for every new module before push
- [ ] Update PLAN.md and NEXT_STEPS.md after every significant run
- [ ] Maintain research docs as the product evolves

Last updated: 2026-11-23 (toolpath spiral strategy)
