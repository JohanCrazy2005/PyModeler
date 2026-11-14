# Development Checklist

Status legend: [ ] Todo  [~] In progress  [x] Done  [-] Deferred

## Phase 0 – Foundation
- [x] Create public GitHub repository
- [x] Define GOAL, PLAN, CHECKLIST, NEXT_STEPS
- [x] Project skeleton with src/, schemas/, tests/, docs/, output/
- [x] JSON Schema for core Mesh data model
- [x] JSON Schema for Scene
- [x] Basic PyQt6 application window that launches
- [x] Cross-platform dependency list (requirements.txt)
- [x] Automated test that the app can start (headless-friendly where possible)
- [x] Continuous integration skeleton (GitHub Actions)
- [x] Ensure all core source modules (mesh, scene, main_window, tests) are fully present and tested on main

## Research & Planning (Mandatory before major new work)
- [x] Create `docs/research/` folder
- [x] Web research: Blender core modeling / mesh / viewport / materials / UV / animation features
- [x] Web research: key features from Maya, 3ds Max, Cinema 4D (as relevant)
- [x] Produce prioritized feature inventory document
- [~] Refine PLAN.md and CHECKLIST with detailed step-by-step items based on research

## Phase 1 – Core Data & Scene
- [x] Full Mesh class with vertices, edges, faces, normals (validated against schema)
- [x] Scene graph (objects, hierarchy, transforms)
- [x] Selection system (object / vertex / edge / face modes) – object mode complete
- [x] Undo/Redo stack (command pattern)
- [x] Basic primitives: Cube, Sphere, Plane, Cylinder, Cone

## Phase 2 – Viewport & Interaction
- [x] OpenGL / moderngl viewport widget inside PyQt6
- [x] Camera (orbit, pan, zoom)
- [x] Grid and axes display
- [x] Object selection in viewport (outliner sync + click-to-select via raycast)
- [x] Transform gizmos (translate / rotate / scale)
- [x] Shading modes (solid, wireframe, solid+edges) + menu
- [x] Standard views (front/side/top) and perspective/ortho toggle
- [x] Full transform (loc/rot/scale) applied in frame and raycast

## Phase 3 – Mesh Editing Tools
- [ ] Extrude
- [ ] Inset / Bevel
- [ ] Loop cut / Knife
- [ ] Boolean operations (via trimesh or manifold)
- [ ] Subdivide / Smooth

## Phase 4 – Materials, UV, I/O
- [ ] Material system (PBR parameters) + schema
- [ ] Texture slots & basic image textures
- [ ] UV editor + simple unwrap
- [ ] Import: OBJ, glTF
- [ ] Export: OBJ, glTF, STL

## Phase 5 – Animation & Advanced
- [ ] Keyframe system
- [ ] Timeline & Dope sheet basics
- [ ] Modifiers (non-destructive)
- [ ] Python console / scripting API
- [ ] Plugin loader

## Ongoing
- [ ] Keep JSON schemas up to date for every new data structure
- [ ] Unit + integration tests for every module before merge
- [ ] Update PLAN.md and NEXT_STEPS.md after every significant run
- [ ] Document user-facing features as they land
- [ ] Maintain research docs as features evolve

Last updated: 2026-11-14 (Phase 2: shading modes, standard views, ortho toggle, full-transform frame/raycast)
