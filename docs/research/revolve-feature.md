# Revolve Feature Research (Parametric CAD)

**Sources**: Autodesk Fusion 360 Help (Revolve solid), Onshape Revolve documentation, community tutorials and FeatureScript examples.

**Date**: 2026-11-15

## Core Concept

A Revolve feature takes one or more closed sketch profiles (or planar faces) and rotates them around a selected axis by an angle (or full 360°) to create a solid body, surface, or thin wall.

This is the primary way parametric CAD systems create rotationally symmetric solids (shafts, bottles, wheels, cups, flanges, etc.).

## Fusion 360 Behavior (summary)

- Select closed sketch profile(s) or planar face.
- Select axis: linear sketch curve, edge, cylindrical face, or construction line.
- **Extent Type**: Partial (angle), To Object, or Full (360°).
- **Direction**: One Side, Two Sides, or Symmetric.
- **Angle**: numeric value or parameter (for Partial).
- **Operation**: New Body, Join, Cut, Intersect.
- Result is a parametric feature in the timeline that recomputes when the driving sketch, axis, or parameters change.

## Onshape Behavior (summary)

- Select sketch regions, sketch entities, or planar faces.
- Select revolve axis: linear sketch entity, edge, cylindrical face, arc, or mate connector.
- Full revolve (360°) by default; uncheck for Blind (angle), Symmetric, or two directions.
- Operations: New, Add, Remove, Intersect.
- Angle and other values are parametric (can reference variables).

## Practical Implementation Priority for PyModeler (Phase 1)

1. **Blind / partial revolve** of a single closed sketch profile (initially rectangle or simple polygon) by an angle (degrees).
2. Angle can be a numeric value **or** a named parameter reference (resolved via ParameterStore).
3. Axis defaults to the sketch plane’s Y-axis (or a simple 3D axis vector) for the first implementation; later support explicit axis selection from sketch entities.
4. Produces a simple solid mesh (faceted solid of revolution for a rectangle profile) that is schema-valid.
5. Feature is serializable via JSON Schema and can be stored in a feature history / timeline.
6. Later increments: full 360°, symmetric, axis from sketch line, non-rectangular profiles with arcs, boolean operations, thin revolve.

This research guides the first RevolveFeature implementation: a schema-driven, parameter-aware feature that turns a Sketch into a solid mesh of revolution.
