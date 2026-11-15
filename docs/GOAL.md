# Project Goal: PyModeler

## Vision
Build a free, open-source, cross-platform **parametric CAD + design-to-manufacture** application in pure Python that works similarly to **Fusion 360**, **Onshape**, and manufacturing-focused tools like **Mozaik**.

The end product should feel like a practical engineering / product-design / small-shop manufacturing tool rather than a pure artistic mesh modeler (Blender-style).

## Target Style & Inspiration (from research)

### Fusion 360-like capabilities
- Parametric (history-based) modeling driven by sketches, dimensions, and constraints
- Direct modeling for imported or quick edits
- Assemblies with relationships / mates
- Sheet metal basics
- Integrated path toward manufacturing (CAM-style thinking: toolpaths, nesting concepts, cut lists)
- Simulation-ready data structures later
- Clean feature tree / timeline

### Onshape-like capabilities
- Strong parametric core with feature history
- Configurations / design variations
- Clean part + assembly workflow
- Version-friendly data model (JSON schemas make this natural)
- Collaboration-ready architecture (even if single-user first)

### Mozaik-like / manufacturing-friendly capabilities
- Automatic cut lists / part lists from designs
- Nesting / material optimization concepts
- Joinery / hardware rules (especially useful for furniture, cabinets, panels)
- Shop drawings / dimensioned outputs
- CNC-ready thinking (G-code generation as a later goal)

## Core Requirements
- **UI Framework**: PyQt6 for native-feeling, cross-platform GUI (Windows, macOS, Linux).
- **Data Models**: All major modules use strict JSON Schemas for validation, serialization, and clean inter-module communication. Feature history, parameters, and constraints must be schema-driven.
- **Libraries**: Prefer mature, well-maintained public Python packages that are cross-platform (numpy, scipy, trimesh, cadquery or similar where helpful, moderngl / PyOpenGL, pillow, jsonschema, etc.).
- **Architecture**: Modular, with clear separation of:
  - Core parametric data (Sketch, Feature, Part, Assembly, Parameters)
  - UI / Viewports / Feature tree
  - I/O (STEP/IGES later, OBJ/glTF, DXF, cut-list exports)
  - Manufacturing helpers (cut lists, nesting stubs, toolpath concepts)
- **Quality**: Code must be tested before every significant push. Prefer clean, typed, documented code.

## Research-First Mandate
Before expanding major feature areas, research the web for how Fusion 360, Onshape, Mozaik, and similar tools implement the feature. Document findings under `docs/research/`. Only then create a detailed step-by-step plan and implement.

## Long-term Capability Targets (prioritized toward CAD/CAM)
1. 2D Sketching with constraints and dimensions
2. Parametric solid features (Extrude, Revolve, Sweep, Loft, Fillet, Chamfer, Shell, Hole…)
3. Feature history / timeline that can be edited and recomputed
4. Assemblies with mates / constraints
5. Configurations and design parameters
6. Basic sheet metal / panel thinking
7. Cut lists, BOMs, and dimensioned drawings
8. Material / stock definitions and simple nesting concepts
9. Path toward CAM (toolpaths, G-code stubs) and manufacturing outputs
10. Clean JSON-schema-driven persistence so designs are transparent and versionable

## Success Criteria
A user can sketch a parametric part, add features driven by dimensions, build a small assembly, generate a cut list or basic manufacturing output, and export usable geometry — in a workflow that feels familiar to someone coming from Fusion 360 or Onshape, with practical manufacturing helpers inspired by tools like Mozaik.

This remains a multi-year project. Progress is incremental and measured by the CHECKLIST and PLAN.
