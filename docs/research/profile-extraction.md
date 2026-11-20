# Profile Extraction from Sketches for Features

Research notes for how Fusion 360 and Onshape turn sketch geometry into closed profiles that can be extruded or revolved.

## Fusion 360

- Profiles are closed regions (loops) detected in the sketch.
- Users select one or more closed sketch profiles (or planar faces).
- Open profiles are visually indicated (small circles at gaps).
- A sketch can contain multiple nested profiles (outer boundary + holes).
- Extrude/Revolve operate on the selected closed area(s).
- Support for lines, arcs, circles, splines that form closed loops.
- Thin extrude allows open profiles with a thickness.

Sources: Autodesk Fusion Help – Solids from sketches, Extrude a solid body.

## Onshape

- When creating a Solid Extrude or Revolve while a sketch is active, Onshape automatically selects all closed regions in the sketch.
- Users can select individual sketch regions or planar faces.
- Supports nested entities (outer profile with inner holes).
- Profiles are used for Extrude, Revolve, Sweep, Loft.
- Closed sketch regions are the primary input for solid features.

Sources: Onshape Help – Extrude, Revolve.

## Implications for PyModeler

Current implementation (updated 2026-11-19):
- Detects simple closed polygons from connected line entities.
- Standalone circles as circular profiles.
- **Arcs are now properly joined into closed loops**: when an arc's computed start/end match existing point entities within tolerance, the arc is discretized and inserted into the polygon points of the cycle.

Next increments:
1. Support for holes / nested profiles (outer + inner regions).
2. Better loop finding for more complex sketches.
3. Non-Y axis support and true solid-of-revolution from profile points for Revolve.

This keeps the mesh-based approach while making feature generation more useful for real sketches that include arcs.
