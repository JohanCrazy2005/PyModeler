# Development Plan

## Guiding Principles
1. **Research First**: Before implementing any major feature area, research how the best tools (Blender, Maya, 3ds Max, Cinema 4D, Houdini) solve the same problem. Document findings under `docs/research/`.
2. **Living Documents**: GOAL.md, CHECKLIST.md, PLAN.md and NEXT_STEPS.md are continuously updated. They are the single source of truth for the automation loop.
3. **Small, Tested Increments**: Prefer complete, tested slices over large incomplete features. Main branch must always remain runnable.
4. **Schema-Driven**: All major data structures (Mesh, Scene, Material, …) are defined by JSON Schemas in `schemas/` and validated at runtime.
5. **Cross-Platform**: Only public, cross-platform Python libraries. PyQt6 for UI.
6. **Clean Architecture**:
   - `schemas/` – source of truth for data contracts
   - `src/pymodeler/core/` – pure data & logic (no Qt)
   - `src/pymodeler/ui/` – PyQt6 views and widgets
   - `src/pymodeler/render/` – viewport drawing
   - `src/pymodeler/io/` – importers/exporters
   - `src/pymodeler/mesh/` – mesh algorithms
   - `docs/research/` – feature research notes from the web
7. **Automation Loop**: An hourly Grok automation reads the current GOAL / CHECKLIST / PLAN / NEXT_STEPS, decides the highest-value next task, implements it, tests it, updates the docs, and pushes.

## Technology Stack (Initial)
- Python 3.10+
- PyQt6 (GUI)
- numpy (geometry)
- jsonschema (validation)
- trimesh (mesh utilities, optional heavy ops)
- moderngl or PyOpenGL (later for viewport)
- pillow (textures)
- pygltflib / gltflib (glTF)
- pytest (testing)

## Process for Every Major Phase / New Feature Area
1. **Web Research**: Search and document features of top modeling softwares relevant to the area.
2. **Synthesize & Prioritize**: Create a clear inventory and priority ranking in docs/ or docs/research/.
3. **Step-by-step Build Plan**: Break the prioritized features into small, testable implementation steps.
4. **Implement + Test + Document**: Code, validate against schemas, write tests, update CHECKLIST and NEXT_STEPS.

## Roadmap Overview (high-level – refined after research)
- **Months 0-2**: Solid foundation – data models, basic UI shell, primitives, simple viewport, selection, transform. (Research mesh tools & viewport capabilities first.)
- **Months 3-6**: Core modeling tools, materials, UV, reliable I/O. (Research each area on the web before coding.)
- **Months 7-12**: Animation, modifiers, scripting, polish.
- Beyond: Advanced features, performance, community plugins.

## Current Focus
1. Research completed for core modeling features and viewport essentials (see `docs/research/`).
2. Foundation modules (Mesh, Scene, MainWindow, schemas, tests) present and tested.
3. Phase 1 complete: primitives, object-mode selection, and Undo/Redo command stack.
4. Phase 2 started: moderngl + QOpenGLWidget viewport with orbit camera, grid, axes, mesh drawing, and selection highlighting.
5. Viewport polish complete (wireframe, lighting/normals, frame-selected/all, click-to-select). Transform gizmos (translate/rotate/scale) implemented with undo support.
6. Additional Phase 2 items done: shading modes (solid / wireframe / solid+edges), standard views, orthographic toggle, full-transform world-space calculations for framing and selection.
7. Gizmo now oriented to object rotation with visual feedback during drag. MainWindow fully functional with Help menu.
8. Phase 3 started: research on Extrude documented; basic region extrude (Mesh.extrude_faces + ExtrudeMeshCommand) implemented and tested. UI wired: Mesh menu + E shortcut extrudes selected objects in object mode along average normal. Improved with individual mode, per-face normals, and better side-face winding (Shift+E). Next: distance/axis UI, then Inset.
9. Prioritized feature inventory drives all future planning.

## Risk Management
- Scope is enormous. Never claim "feature complete" until checklist items are truly done and tested against the researched inventory.
- Prefer wrapping existing mature libraries over re-implementing complex algorithms from scratch.
- Keep the main branch always runnable.
