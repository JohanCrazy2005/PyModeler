# Assembly Model Research Notes

Research for PyModeler simple Assembly data model. Sources: Autodesk Fusion Help (Assemblies, Components, Joints), Onshape Learning Center (Mating Basics, Instances), Fusion 360 Gallery Dataset assembly docs. Last updated: 2026-11-17.

## Fusion 360 / Autodesk Fusion
- An **Assembly** is a collection of **Components** that function as a single design.
- Components can be internal or external (linked). A component acts as a container for sketches, bodies, construction geometry, and can contain other components (sub-assemblies).
- **Occurrences** (instances) of components are placed in the assembly. Each occurrence has a transform (position, orientation, scale) relative to its parent.
- Relationships: Joints (revolute, slider, etc.), Constraints, As-Built Joints, Rigid Groups. These define degrees of freedom and motion.
- Hierarchy via the browser/tree. Grounding anchors a component.
- BOM and manufacturing outputs derive from the assembly structure.

## Onshape
- Assemblies are separate from Part Studios.
- **Instances** of parts (or other assemblies) are inserted into an Assembly.
- Positioning and motion via **Mates** that align **Mate Connectors** (local coordinate systems on parts).
- Common mates: Fastened (rigid), Revolute, Slider, etc. Groups lock relative positions.
- Instances list shows all parts, sub-assemblies, mates, and connectors.
- Fix grounds an instance. Sub-assemblies can be locked.

## Key Concepts for PyModeler (Phase 2 start)
- Assembly owns a list of **Instances**.
- Each Instance references a Part (by id) and stores a **Transform** (location + Euler rotation + scale).
- Optional flags: grounded / fixed, visible, name override.
- Mates / joints are deferred (future schema extension: list of mate objects that reference instance ids and constrain relative transforms).
- Supports simple hierarchical placement for visualization, cut lists of the whole assembly, and later constraint solving.
- Data must validate against JSON Schema so designs stay transparent and versionable.

## Implementation Plan (this increment)
1. `schemas/assembly.schema.json` – Assembly with instances array.
2. `src/pymodeler/core/assembly.py` – Assembly and Instance classes, validation, add/remove, serialization.
3. Tests covering creation, validation, round-trip, and basic transform storage.
4. Research note (this file) + update living docs.

Mates, motion, and full constraint solving come in later increments.
