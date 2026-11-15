# Extrude Feature Research (Parametric CAD)

**Sources**: Autodesk Fusion 360 Help (Extrude solid / surface), Onshape Extrude documentation and tech tips, community tutorials.

**Date**: 2026-11-15

## Core Concept

An Extrude feature takes one or more closed sketch profiles (or planar faces) and sweeps them along a straight direction (normally the sketch plane normal) by a distance (or to a geometric limit) to create a solid body, surface, or thin wall.

This is the primary way parametric CAD systems turn 2D sketches into 3D solids.

## Fusion 360 Behavior (summary)

- Select closed sketch profile(s) or planar face.
- **Type**: Extrude (solid) or Thin Extrude.
- **Start**: Profile Plane (default), Offset, or Object.
- **Direction**: One Side, Two Sides, or Symmetric (Half Length / Whole Length).
- **Extent**: Distance (numeric or parameter), To Object, All, etc.
- **Operation**: New Body, Join, Cut, Intersect.
- Distance can be driven by user parameters / expressions.
- Result is a parametric feature in the timeline that recomputes when the driving sketch or parameters change.

## Onshape Behavior (summary)

- Select sketch regions, sketch entities, or planar faces.
- End types: Blind (distance), Symmetric, Up to next / face / part / vertex, Through all.
- Optional Starting Offset.
- Direction can be overridden by a selected line / plane / mate connector.
- Draft angle optional.
- Operations: New, Add, Remove, Intersect.
- Depth and offsets are parametric (can reference variables).

## Practical Implementation Priority for PyModeler (Phase 1)

1. **Blind extrude** of a single closed sketch profile (initially rectangle or simple polygon) by a distance.
2. Distance can be a numeric value **or** a named parameter reference (resolved via ParameterStore).
3. Direction defaults to the sketch plane normal (positive Z for default XY plane).
4. Produces a simple solid mesh (box for rectangle, extruded prism for polygon) that is schema-valid.
5. Feature is serializable via JSON Schema and can be stored in a feature history / timeline.
6. Later increments: symmetric, two-sided, start offset, To Object, boolean operations, thin extrude, non-rectangular profiles with arcs.

This research guides the first ExtrudeFeature implementation: a schema-driven, parameter-aware feature that turns a Sketch into a solid mesh.
