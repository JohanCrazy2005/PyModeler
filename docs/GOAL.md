# Project Goal: PyModeler

## Vision
Build a free, open-source, cross-platform 3D modeling application in pure Python that eventually matches the core capabilities of leading commercial and open-source modeling softwares (Blender, Maya, 3ds Max, Cinema 4D, Houdini basics, etc.).

## Core Requirements
- **UI Framework**: PyQt6 for native-feeling, cross-platform GUI (Windows, macOS, Linux).
- **Data Models**: All major modules use strict JSON Schemas for validation, serialization, and clean inter-module communication.
- **Libraries**: Prefer mature, well-maintained public Python packages that are cross-platform (numpy, scipy, trimesh, moderngl / PyOpenGL, pillow, jsonschema, pygltflib, etc.).
- **Architecture**: Modular, plugin-friendly, with clear separation of:
  - Core data (Scene, Mesh, Material, Object)
  - UI / Viewports
  - I/O (import/export)
  - Rendering / Viewport drawing
  - Tools & Operators
- **Quality**: Code must be tested before every significant push. Prefer clean, typed, documented code.

## Research-First Mandate
Before expanding major feature areas, the project (and every automation run that starts a new phase) **must first research the web** for comprehensive feature lists of top modeling software. Document findings in `docs/research/` (or update this GOAL and PLAN). Only after a clear, prioritized feature inventory exists should detailed step-by-step implementation planning and coding begin.

Sources to consult (examples):
- Official Blender manual / feature overview
- Autodesk Maya documentation / feature lists
- 3ds Max, Cinema 4D, Houdini feature pages
- Wikipedia and comparison articles on 3D modeling software
- Community lists of essential modeling tools

The goal is a realistic, complete inventory of capabilities so the build plan is grounded in what real top-tier tools actually provide.

## Long-term Capability Targets (initial high-level list – to be expanded/refined via research)
1. Mesh creation & editing (primitives, extrude, bevel, loop cut, boolean, etc.)
2. Scene hierarchy / outliner
3. Materials & textures (PBR basics)
4. UV unwrapping & mapping
5. Basic animation & keyframing
6. Viewport navigation, selection, gizmos
7. Import/Export: OBJ, glTF/GLB, FBX (via libraries), STL, PLY
8. Modifiers stack (non-destructive)
9. Sculpting basics (later)
10. Simple rendering / path tracing integration or offline render
11. Python scripting API for users
12. Add-on / plugin system

## Success Criteria for "Complete"
The application is considered to have "all the capabilities the top modeling softwares have" when a professional modeler can create, edit, texture, UV, animate basic objects, and export production-ready assets without needing another tool for core modeling tasks — as validated against the researched feature inventory.

This is a multi-year ambitious project. Progress is incremental, measured by the CHECKLIST and PLAN.
