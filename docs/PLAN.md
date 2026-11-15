# Master Development Plan

## Guiding Principles
1. **Research First, Then Plan, Then Build**: Before any major new area, research how Fusion 360, Onshape, and Mozaik (and related tools) implement it. Document under `docs/research/`. Then write a concrete step-by-step plan. Only then code.
2. **Parametric CAD First**: The core is a history-based parametric modeler (sketches → features → parts → assemblies), not freeform mesh sculpting.
3. **JSON Schema First**: Every persistent structure (Sketch, Feature, Part, Assembly, Parameter, CutList…) has a formal JSON Schema.
4. **Test Before Push**: Main branch must stay runnable and tested.
5. **Incremental & Visible Progress**: Small, complete, tested features.
6. **Cross-platform**: Windows, macOS, Linux via public Python libraries + PyQt6.
7. **Design-to-Manufacture Mindset**: Even early features should keep manufacturing usefulness in mind (parameters, cut lists, clear part definitions).

## Architecture (updated for CAD focus)
- `schemas/` – Sketch, Feature, Part, Assembly, Parameter, Material, CutList, etc.
- `src/pymodeler/core/` – pure parametric logic (no Qt)
- `src/pymodeler/ui/` – PyQt6 (feature tree, viewport, property panels, sketch editor)
- `src/pymodeler/render/` – viewport
- `src/pymodeler/io/` – import/export + manufacturing outputs
- `src/pymodeler/cam/` or manufacturing helpers (later)
- `docs/research/` – feature research notes from Fusion / Onshape / Mozaik

## Technology Stack (Initial + CAD direction)
- Python 3.10+
- PyQt6
- numpy, scipy
- jsonschema
- trimesh (mesh utilities)
- Consider CadQuery / OCP / pythonOCC later for robust B-Rep if needed
- moderngl or PyOpenGL for viewport
- pytest

## Process for Every Major Phase
1. Web research of Fusion 360 / Onshape / Mozaik behavior for that area.
2. Write structured notes in `docs/research/`.
3. Produce prioritized, step-by-step implementation plan.
4. Implement + schema + tests + update living docs.

## High-level Roadmap (CAD/CAM oriented)
- **Phase 0-1 (Foundation)**: Project structure, basic scene, simple solids, PyQt6 shell, research documents. (mostly complete)
- **Phase 2 (Sketch + Parametric Core)**: 2D sketch engine with constraints/dimensions, Extrude/Revolve, feature history.
- **Phase 3 (Parts & Assemblies)**: Multi-feature parts, basic assemblies and mates.
- **Phase 4 (Manufacturing Helpers)**: Cut lists, BOMs, simple nesting concepts, dimensioned outputs (Mozaik-inspired).
- **Phase 5 (Advanced + CAM path)**: Sheet metal basics, configurations, early toolpath / G-code stubs, simulation data.

## Current Focus
1. Research on parametric modeling (Fusion/Onshape) and manufacturing features (Mozaik) is complete and documented.
2. Sketch data model + JSON Schema is implemented and tested (entities, constraints, dimensions).
3. Parameter / variable system implemented and tested (named params, simple expressions).
4. Extrude feature + FeatureHistory data model implemented and tested (parameter-driven distance, simple solid generation).
5. Timeline/feature tree UI stub implemented (list + property panel). Next: basic sketch editor widgets, then Revolve.

## Risk Management
- Scope is still large. Stay focused on parametric CAD + practical manufacturing helpers.
- Prefer proven libraries for geometry kernels when the pure-Python approach becomes limiting.
- Main branch always runnable.
- Constraint solving and robust B-Rep are non-trivial; start with simple validated sketches and mesh-based solids before investing in heavy kernels.
