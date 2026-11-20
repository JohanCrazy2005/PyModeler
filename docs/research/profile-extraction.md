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

Current implementation (updated 2026-11-20):
- Detects simple closed polygons from connected line entities.
- Standalone circles as circular profiles.
- **Arcs are now properly joined into closed loops**: when an arc's computed start/end match existing point entities within tolerance, the arc is discretized and inserted into the polygon points of the cycle.
- **Nested holes**: after extraction, polygons are sorted by area; containment is tested with ray-casting point-in-polygon on the centroid of candidate inners. Contained polygons are attached as the "holes" list on the outer; only top-level profiles are returned.

Next increments:
1. Use hole profiles in Extrude mesh generation (subtract holes from solid).
2. Better loop finding for more complex sketches.
3. Non-Y axis support and true solid-of-revolution from profile points for Revolve.

This keeps the mesh-based approach while making feature generation more useful for real sketches that include arcs and holes.

## Update 2026-11-20: Nested holes

- After extracting closed polygons (including those with discretized arcs inserted), profiles are sorted by area.
- Containment is tested via ray-casting point-in-polygon on the centroid of candidate inner polygons.
- Contained polygons are attached as the "holes" list on the outer profile; only top-level profiles are returned.
- Circles remain independent for now.
- This enables future Extrude/Revolve to cut holes from the solid.

Sources: Fusion 360 and Onshape profile/region selection behavior (outer region with inner loops).
