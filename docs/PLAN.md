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
- `schemas/` – Sketch, Feature, Part, Assembly, Parameter, Material, CutList, etc.
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

## Current Status (2026-11-17)
- Phase 0 + Phase 1 complete (Sketch, Parameters, Extrude, Revolve, FeatureHistory, canvas tools, DOF stub, Booleans).
- Phase 2: **Part model** + **Material / stock definitions** implemented and tested.
- Next: Cut-list stub, light UI wiring of Parts, then Assembly.

## Near-term Roadmap
1. Cut-list generator (walk Parts → list of parts with dimensions + material lookup).
2. MainWindow / FeatureTree integration so the user works with Parts instead of a free-floating FeatureHistory.
3. Simple Assembly data model (list of Part instances + transforms; mates later).
4. DXF export stub for 2D profiles / drawings using ezdxf.
5. Viewport polish and selection.

Keep PLAN, CHECKLIST, and NEXT_STEPS synchronized after every significant run.
