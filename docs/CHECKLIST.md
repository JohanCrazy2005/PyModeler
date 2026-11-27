# PyModeler Checklist

Living checklist synchronized with PLAN.md and NEXT_STEPS.md.
Mark completed items. Prefer Phase 1 → Phase 2 → etc.

## Phase 0 – Foundation
- [x] Project structure, schemas/, src layout, PyQt6 skeleton
- [x] JSON Schema validation infrastructure
- [x] Basic Mesh / Scene / Part data models
- [x] FeatureHistory core

## Phase 1 – Sketch + Basic Features
- [x] 2D Sketch (points, lines, arcs, constraints schema)
- [x] Parameters / expression evaluator (arithmetic + trig/units)
- [x] Lightweight 2D constraint solver stub (scipy least_squares)
- [x] Extrude feature (profile-based mesh, holes, symmetric)
- [x] Revolve feature (solid of revolution, arbitrary axis)
- [x] Feature tree UI + rollback
- [x] Sketch editor canvas tools

## Phase 2 – Part / Assembly / Manufacturing Data
- [x] Part model + material/stock
- [x] Cut list generation + exports
- [x] Assembly mates (rigid/fastened + revolute/slider stubs)
- [x] BOM
- [x] DXF import/export (ezdxf)
- [x] Configurations
- [x] Multi-part UI
- [x] Assembly viewport visualization
- [x] Configuration selection UI

## Phase 3 – Viewport Polish
- [x] RGB axes, shading modes, standard views, orthographic
- [x] Keyboard shortcuts for views/frame
- [x] Selection outline + gizmo visuals (arrowheads, rings)
- [x] Gizmo hit-testing + drag feedback
- [x] Parametric-intent transforms (translate/scale/rotate update sketch/params)
- [x] Constraint-aware transforms

## Phase 4 – Advanced Features + Early CAM
- [x] HoleFeature (parametric, direction, Boolean cut)
- [x] Fillet / Chamfer stubs + basic mesh bevel
- [x] Shell feature (normal offset + walls + corner mitering)
- [x] UI property panel exposure for Fillet/Chamfer/Shell/Hole params
- [x] Sheet-metal rule schema + bend allowance helper
- [x] Rectangular NestingJob + shelf packer + multi-sheet + UI preview
- [x] ToolpathJob schema + rectangular pocket/contour
- [x] Concentric + zigzag + continuous rectangular spiral strategies
- [x] Spiral strategy with optional corner-radius arcs (G03)
- [x] Linear lead-in/out + corner-radius G03 arcs
- [x] Toolpath preview dialog wired to Manufacturing menu
- [x] Full unit system with suffixes in expressions (length + angle)
- [x] Viewport-based edge/face picking (pure ray hit helpers + mode + property panel feed)
- [x] True Archimedean spiral toolpath (polar, inscribed circle)
- [x] Morphing spiral toolpath (linear morph of Archimedean following rectangular bound)
- [x] Robust manifold/Boolean repair when manifold3d available
- [x] Better shell openings (explicit rim walls + named face ids)
- [x] Basic DXF import (LINE/CIRCLE/ARC to Sketch)
- [x] Viewport picking polish (multi-select Shift, highlight edges/faces, basic box select, select-other cycle via ~)
- [x] Import/export improvements – bulge-aware LWPOLYLINE + POLYLINE (virtual_entities → ARC/LINE); STEP later
- [x] Optional Boolean-based shell offset when engine available
- [x] DXF import: SPLINE/ELLIPSE approximation + TEXT stub
- [x] DXF dimension export (length + radius + diameter + angular + aligned + ordinate DIMENSION entities)
- [x] Better dimension placement (user offset / side / angle + value-driven defaults)
- [x] Ordinate / aligned dimension variants for manufacturing drawings
- [x] Basic DIMENSION import recovery into sketch dimensions (length/aligned/radius/diameter/ordinate)
- [x] Improved DIMENSION matching / angular recovery (2-line angular via defpoint pairing)
- [x] Improved line matching (point-to-segment) + 3-point angular DIMENSION recovery stub
- [x] Sketch editor: full dimension types (length/distance/radius/diameter/angle/aligned/ordinate)
- [x] Ordinate group UI ("Add Ordinate Group") + group_id / leader_style on dimensions
- [x] Dimensions table Params column (axis/origin/offset/group/leader)
- [x] Restored sketch_canvas.py from last good revision (was empty on main) — actually written as minimal QGraphicsView stub this run
- [x] Sketch canvas: visual drawing of points/lines/circles/arcs + modes + snapping + selection highlight
- [x] Leader style UI control (dropdown) + export respect for leader_style on ordinate/aligned dims
- [x] Canvas mode toolbar in SketchEditor + dimension labels on canvas + midpoint snapping
- [x] Arc mode full mouse interaction on canvas (3-click center → start/radius → end angle + live preview)
- [x] Fixed SketchCanvas QPainter.RenderHint.Antialiasing (PyQt6 compatibility)
- [x] 3-point arc mode (arc3): start → through → end, circle fit, CCW ordering, live preview, editor combo
- [x] Canvas multi-select (Shift) + box select for sketch entities (parity with viewport)
- [x] Canvas constraint and dimension badges (text labels near entities)

## Ongoing
- [ ] Keep all major modules schema-validated
- [ ] Tests pass before push (headless UI tests guarded)
- [ ] Research notes under docs/research/ for new areas
- [ ] Living docs (CHECKLIST / PLAN / NEXT_STEPS) updated every run

Last updated: 2026-11-27 (canvas constraint and dimension badges)
