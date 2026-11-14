# Master Development Plan

## Guiding Principles
1. **JSON Schema First**: Every persistent or inter-module data structure has a formal JSON Schema. Validate on load/save and at module boundaries.
2. **Test Before Push**: No code reaches the main branch without automated tests that pass.
3. **Incremental & Visible Progress**: Each automation run should leave the repo in a better, working state. Prefer small, complete features over large incomplete ones.
4. **Cross-platform from Day 1**: Use only libraries that work on Windows, macOS, and Linux. Prefer pure-Python or widely available wheels.
5. **Clean Architecture**:
   - `schemas/` – source of truth for data contracts
   - `src/pymodeler/core/` – pure data & logic (no Qt)
   - `src/pymodeler/ui/` – PyQt6 views and widgets
   - `src/pymodeler/render/` – viewport drawing
   - `src/pymodeler/io/` – importers/exporters
   - `src/pymodeler/mesh/` – mesh algorithms
6. **Automation Loop**: An hourly Grok automation reads the current GOAL / CHECKLIST / PLAN / NEXT_STEPS, decides the highest-value next task, implements it, tests it, updates the docs, and pushes.

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

## Roadmap Overview
- **Months 0-2**: Solid foundation – data models, basic UI shell, primitives, simple viewport, selection, transform.
- **Months 3-6**: Core modeling tools, materials, UV, reliable I/O.
- **Months 7-12**: Animation, modifiers, scripting, polish.
- Beyond: Advanced features, performance, community plugins.

## Current Focus (Phase 0 → Phase 1)
Finish a minimal but working application that:
1. Opens a PyQt6 window.
2. Can create a Cube mesh validated by schema.
3. Displays basic info / outliner.
4. Has a clean project layout and documentation that the automation can continue from.

## Risk Management
- Scope is enormous. Never claim "feature complete" until checklist items are truly done and tested.
- Prefer wrapping existing mature libraries over re-implementing complex algorithms from scratch.
- Keep the main branch always runnable.
