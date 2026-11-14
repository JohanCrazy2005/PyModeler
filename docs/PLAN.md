# Master Development Plan

## Guiding Principles
1. **Research First, Then Plan, Then Build**: Before implementing major new capability areas, research the web for the full feature sets of top modeling software (Blender, Maya, 3ds Max, Cinema 4D, etc.). Document findings. Only then create or refine a detailed step-by-step plan. Coding follows the plan.
2. **JSON Schema First**: Every persistent or inter-module data structure has a formal JSON Schema. Validate on load/save and at module boundaries.
3. **Test Before Push**: No code reaches the main branch without automated tests that pass.
4. **Incremental & Visible Progress**: Each automation run should leave the repo in a better, working state. Prefer small, complete features over large incomplete ones.
5. **Cross-platform from Day 1**: Use only libraries that work on Windows, macOS, and Linux. Prefer pure-Python or widely available wheels.
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
1. Research completed for core modeling features (see `docs/research/`).
2. Foundation modules (Mesh, Scene, MainWindow, schemas, tests) restored and present.
3. Next: remaining primitives, then real viewport.
4. Prioritized feature inventory drives all future planning.

## Risk Management
- Scope is enormous. Never claim "feature complete" until checklist items are truly done and tested against the researched inventory.
- Prefer wrapping existing mature libraries over re-implementing complex algorithms from scratch.
- Keep the main branch always runnable.
