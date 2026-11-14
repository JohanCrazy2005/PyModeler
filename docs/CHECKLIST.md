# Development Checklist

Status legend: [ ] Todo  [~] In progress  [x] Done  [-] Deferred

## Phase 0 – Foundation (Current)
- [x] Create public GitHub repository
- [x] Define GOAL, PLAN, CHECKLIST, NEXT_STEPS
- [x] Project skeleton with src/, schemas/, tests/, docs/, output/
- [x] JSON Schema for core Mesh data model
- [x] JSON Schema for Scene
- [x] Basic PyQt6 application window that launches
- [x] Cross-platform dependency list (requirements.txt)
- [x] Automated test that the app can start (headless-friendly where possible)
- [ ] Continuous integration skeleton (GitHub Actions)

## Phase 1 – Core Data & Scene
- [ ] Full Mesh class with vertices, edges, faces, normals (validated against schema)
- [ ] Scene graph (objects, hierarchy, transforms)
- [ ] Selection system (object / vertex / edge / face modes)
- [ ] Undo/Redo stack (command pattern)
- [ ] Basic primitives: Cube, Sphere, Plane, Cylinder, Cone

## Phase 2 – Viewport & Interaction
- [ ] OpenGL / moderngl viewport widget inside PyQt6
- [ ] Camera (orbit, pan, zoom)
- [ ] Grid and axes display
- [ ] Object selection in viewport
- [ ] Transform gizmos (translate / rotate / scale)

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

Last updated: 2026-11-14 (initial)
