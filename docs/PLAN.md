# Master Development Plan

## Guiding Principles
1. **Research First, Then Plan, Then Build**: Before any major new area, research how Fusion 360, Onshape, and Mozaik (and related tools) implement it. Document under `docs/research/`. Then write a concrete step-by-step plan. Only then code.
2. **Schema-Driven Data**: Every major module has a JSON Schema. Validate on construction and serialization.
3. **PyQt6 UI**: Cross-platform native feel.
4. **Test Before Push**: Main branch must stay runnable and tested.
5. **Incremental & Visible Progress**: Small, complete, tested features.
6. **Cross-platform**: Windows, macOS, Linux via public Python libraries + PyQt6.
7. **Design-to-Manufacture Mindset**: Even early features should keep manufacturing usefulness in mind (parameters, cut lists, clear part definitions).

## Architecture (updated for CAD focus)
- `schemas/` – Sketch, Feature, Part, Assembly, Parameter, Material, CutList, SheetMetalRule, NestingJob, ToolpathJob, etc.
- `src/pymodeler/core/` – pure parametric logic (no Qt)
- `src/pymodeler/ui/` – PyQt6 (feature tree, viewport, property panels, sketch editor)
- `src/pymodeler/render/` – viewport
- `src/pymodeler/io/` – import/export + manufacturing outputs (DXF via ezdxf)
- `src/pymodeler/cam/` or manufacturing helpers (later)
- `docs/research/` – feature research notes from Fusion / Onshape / Mozaik

## Technology Stack
- Python 3.10+
- PyQt6
- numpy, scipy
- jsonschema
- trimesh (mesh utilities + basic Booleans)
- **ezdxf** (DXF read/write — approved and preferred)
- moderngl / PyOpenGL for viewport
- Optional: manifold3d for robust Booleans, CadQuery / OCP later for B-Rep

## Current Status (2026-11-27)
- Done: Canvas constraint and dimension badges (simple text labels H/V/C/= etc. and type:value near midpoints/centers, tooltips, data(1) marker).
- Done: Canvas multi-select (Shift toggle) + rubber-band box select for sketch entities (parity with viewport).
- Done: Arc mode full mouse interaction on canvas (3-click center → radius/start-angle → end-angle with live preview).
- Done: Canvas mode toolbar wiring in SketchEditor + dimension value labels on canvas + midpoint snapping.
- Done: Leader style UI control + DXF export respect for ordinate/aligned dimensions.
- Done: Improved DIMENSION matching / angular recovery — `_import_dimensions` handles 2-line angular (dimtype 2) by pairing defpoints to match or create lines and add angle dimension (research updated in docs/research/dxf-dimension-export.md).
- Done: Basic DIMENSION import recovery — `import_dxf_to_sketch` recovers length/aligned/radius/diameter/ordinate dimensions from DXF via get_measurement() + definition-point matching (research updated in docs/research/dxf-dimension-export.md).
- Done: DXF import of SPLINE/ELLIPSE (polyline approx) + TEXT stub (metadata).
- Done: Optional Boolean-based shell offset for closed inside shells (centroid-scale inner solid + mesh_boolean cut when engine available; fallback to wall-stitching). Research in docs/research/shell-boolean-offset.md.
- Done: DXF import improved – bulge-aware LWPOLYLINE + POLYLINE via virtual_entities (ARC for curves); research in docs/research/dxf-export.md.
- Done: Viewport edge/face picking + polish (ray hit helpers, selection modes, multi-select, highlight, box, select-other); research in docs/research/viewport-edge-face-picking.md.
- Done: Spiral toolpath supports corner-radius arcs (G03) and true Archimedean / morphing variants; research in docs/research/toolpath-spiral.md.
- Done: Full unit system with suffixes in expressions (numeric literals + length units mm/cm/m/in/ft expanded to base mm; angle units deg/rad expanded to degrees; pi/e supported; research in docs/research/unit-suffixes.md).
- Done: Lightweight 2D constraint solver stub (scipy.optimize.least_squares for basic geometric constraints + driving dimensions length/distance/radius/diameter/angle + free radii + parameter name evaluation for string dimension values + full arithmetic expression evaluation for dimension values + trig / unit-aware functions (sin/cos in degrees, sqrt, pi, in_to_mm, ...) + Sketch.solve()).
- Done: Shell corner mitering (per-vertex miter scale so offset approximates constant thickness at sharp corners).
- Done: UI exposure for edges/faces selection on Fillet/Chamfer/Shell (property panel text field parsing comma-separated indices/IDs).
- Done: Early toolpath / G-code (ToolpathJob schema + rectangular pocket & contour + zig-zag + continuous rectangular spiral + linear lead-in/out + corner_radius G03 arcs + true Archimedean polar spiral on inscribed circle). Full implementation restored. ToolpathPreviewDialog wired into Manufacturing menu. Continuous spiral now emits single-plunge continuous inward path per Z level.
- Done: Rectangular nesting (NestingJob + shelf packer + from-cutlist + from-parts helper + multi-sheet-size + UI preview wired to live parts with sample fallback).
- Phase 0 + Phase 1 complete (Sketch, Parameters, Extrude, Revolve with real solid-of-revolution from profile points, FeatureHistory, canvas tools, DOF stub, Booleans).
- Phase 2: Part model + Material/stock + Cut-list + Assembly mates + BOM + DXF + multi-part UI + UI exposure of mates/BOM/cut-list exports + Configurations (independent inputs) + Assembly viewport visualization + Configuration selection UI complete.
- Phase 3: Viewport polish (RGB axes, shading modes, standard views, orthographic toggle, keyboard frame/views, selection clear-on-miss, full transform paint path) complete. Selection outline (edge highlight) and richer gizmo visuals (arrowheads + rotation rings) added. Parametric-intent translation, scale, and rotate on gizmo commit are complete (sketch offset/scale/dimensions + plane axes + recompute). Gizmo hit-testing prefers tips/rings with drag highlight.
- Phase 4 started and largely advanced: HoleFeature (schema, parametric diameter/depth, center, cylindrical tool mesh, FeatureHistory integration, Boolean cut against part body). Research documented in docs/research/hole-feature.md. Extrude symmetric mesh generation also corrected. FilletFeature stub (schema, parametric radius, edge list, placeholder mesh, FeatureHistory). Research in docs/research/fillet-feature.md. ChamferFeature stub (schema, parametric distance, edge list, placeholder cone mesh, FeatureHistory). Research in docs/research/chamfer-feature.md. Profile extraction improved: arcs now join into closed loops when start/end match points (discretized into polygon). Nested holes: outer polygons receive contained inner polygons as holes list. True solid-of-revolution: RevolveFeature now generates a lathe mesh from polygon profile points around the Y-axis, with partial-angle end caps.
- Done: through-all extents for Hole. Done: basic mesh bevel for Fillet/Chamfer. Done: hole profiles used in Extrude. Done: arbitrary axis for Revolve. Done: Chamfer modes (equal / two-distance / distance-angle) in schema + apply path with basic bevel stub. Done: Hole direction vector orientation (Rodrigues rotation of tool cylinder). Done: Shell feature (schema + FeatureHistory + basic mesh shell approximation via normal-offset + walls).
- Done: Hole direction exposed in property panel (diameter, depth, direction vector editor).
- Done: Fillet / Chamfer / Shell property panel UI exposure (radius, mode + secondary, thickness, direction).
- Done: Constraint-aware parametric transforms (translation/scale skip locked points and coincident components with fixed points; radii scaled only for unlocked centers).
- Done: Improved bevel quality (adjacent-face normal offsets, corner fans, multi-segment support, optional vertex-merge / degenerate cleanup).
- Done: Early sheet-metal / panel thinking — research notes + SheetMetalRule schema + store + bend_allowance helper + starter rules.
- Done: Robust manifold/Boolean repair when manifold3d available.
- Done: Better shell openings (explicit rim walls + named face ids).

## Near-term Roadmap
1. (done) Visualize assembly instances in the viewport (apply transforms).
2. (done) UI for selecting configuration values.
3. (done) Richer mate solver (matrix composition for rigid/fastened + revolute/slider stubs).
4. (done) Selection outline + richer gizmo visuals (arrowheads, rotation rings).
5. (done) Full transform (rotation + scale) in viewport drawing + paint path.
6. (done) Real profile-based Extrude and Revolve mesh generation (solid of revolution from points).
7. (done for translate/scale/rotate) Transform tools that update driving parameters or sketch entities when possible.
8. (done) Gizmo hit-testing polish + drag visual feedback.
9. (done) Hole feature stub (schema + tool mesh).
10. (done) Integrate Hole into Boolean cut against part solid.
11. (done) Fillet feature stub (schema + placeholder).
12. (done) Chamfer feature stub (schema + placeholder).
13. (done) Profile extraction improvements (arcs into loops, holes).
14. (done) Basic mesh bevel approximation for Fillet/Chamfer.
15. (done) Hole profiles used in Extrude mesh generation (subtract nested holes).
16. (done) Sheet-metal rule schema + bend-allowance helper.
17. (done) Rectangular nesting job.
18. (done) Early toolpath / G-code stubs.
19. (done) Zig-zag pocket strategy for toolpaths.
20. (done) Shell corner mitering.
21. (done) UI edges/faces selection for Fillet/Chamfer/Shell.
22. (done) Lightweight constraint solver stub (with driving dimensions + parameter evaluation + arithmetic expressions + trig/unit functions).
23. (done) Toolpath linear lead-in / lead-out.
24. (done) Toolpath spiral pocket strategy.
25. (done) Spiral with corner-radius arcs.
26. (done) Viewport-based edge/face picking for Fillet/Chamfer/Shell.
27. (done) Viewport picking polish.
28. (done) True Archimedean + morphing spiral toolpaths.
29. (done) DXF bulge-aware polyline import.
30. (done) DXF DIMENSION export (length + radius + diameter + angular + aligned + ordinate).
31. (done) Basic DIMENSION import recovery into sketch dimensions.
32. (done) Improved DIMENSION matching / angular recovery.
33. (done) Multi-feature ordinate dimension groups (`add_ordinate_group`).
34. (done) Full DXF I/O module restored and verified.
35. (done) Canvas mode toolbar + dimension labels + midpoint snap.
36. (done) Arc mode full mouse interaction on canvas.
37. (done) Canvas multi-select (Shift) + box select for sketch entities.
38. (done) Canvas constraint and dimension badges.

Keep PLAN, CHECKLIST, and NEXT_STEPS synchronized after every significant run.

Last updated: 2026-11-27 (canvas constraint and dimension badges)
