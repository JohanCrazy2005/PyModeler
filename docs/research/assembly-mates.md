# Assembly Mates / Joints Research Notes

Research for PyModeler basic Assembly mates (rigid / fastened). Sources: Autodesk Fusion Help (Joints, Rigid Groups), Onshape Learning Center (Mating Basics, Fastened mate). Last updated: 2026-11-17.

## Fusion 360 / Autodesk Fusion
- Uses **Joints** (and Constraints) rather than traditional multi-mate stacks.
- **Rigid Joint**: 0 degrees of freedom. Locks two components so they behave as a single fixed unit (no relative translation or rotation).
- Also supports Rigid Groups that lock multiple components together.
- As-Built Joints capture the current relative position and define motion type without moving parts.
- Other joints (Revolute, Slider, Cylindrical, etc.) open specific DOFs; Rigid is the simplest fixed connection.

## Onshape
- Assemblies use **Mates** that align **Mate Connectors** (local coordinate systems).
- **Fastened** mate: removes all 6 degrees of freedom. Parts are completely bonded; relative position is fixed.
- Most common mate type for rigid connections (bolts, welded parts, fixed sub-assemblies).
- Other mates (Revolute, Slider, Cylindrical, Planar, Ball, …) leave specific DOFs free.
- A single Fastened mate often replaces several traditional coincident/concentric/parallel mates.

## Key Concepts for PyModeler (this increment)
- Extend the Assembly data model with a list of **mates**.
- Each mate references two instances (`instance_a`, `instance_b`) and a type.
- Supported types this increment: `"rigid"` and `"fastened"` (treated identically — both enforce a fixed relative transform).
- Store an optional **offset** transform that describes the desired relative placement of B with respect to A.
- Provide a simple solver that, given grounded instances as anchors, updates free instance transforms so rigid/fastened mates are satisfied (basic translation offset for now; full 6-DOF composition later).
- Schema-driven so mates are versionable and validated.

## Implementation Plan (this increment)
1. Update `schemas/assembly.schema.json` with optional `mates` array.
2. Add `Mate` class and solver helper in `src/pymodeler/core/assembly.py`.
3. Tests for schema validation, round-trip, and basic rigid solve.
4. Update living docs and research note (this file).

Future increments: revolute/slider, full transform composition, UI exposure, motion simulation.

## Update 2026-11-19 – Richer solver
- Rigid/fastened now use full 4x4 matrix composition (world_B = world_A @ offset) with Euler extraction.
- Revolute and slider types are accepted as stubs (apply fixed offset; full DOF later).
- Tests cover rotation composition and stub acceptance.

