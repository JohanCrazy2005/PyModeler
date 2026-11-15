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

Current implementation only handles axis-aligned bounding boxes of points (simple rectangles) and falls back to a cube/cylinder.

Next increments:
1. Detect simple closed polygons formed by connected line entities.
2. Support circle entities as circular profiles (faceted).
3. Discretize arcs into polyline segments for inclusion in profiles.
4. Later: full region detection with holes, proper loop finding.

This keeps the mesh-based approach while making feature generation more useful for real sketches.
