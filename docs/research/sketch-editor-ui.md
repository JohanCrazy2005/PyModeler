# Sketch Editor UI Research

## Sources
- Autodesk Fusion 360 Help: Sketches, Constraints, Dimensions (help.autodesk.com)
- Onshape Help: Sketch Basics, Defining and Constraining Sketches (cad.onshape.com)
- Onshape blog: Under The Hood: Onshape Sketches

## Key Observations from Fusion 360
- Sketch contextual tab appears when creating/editing a sketch.
- Sketch Palette dialog controls visibility of dimensions, constraints, profiles, points, grid, snap.
- Dimensions are created with Sketch Dimension tool; double-click to edit value/expression.
- Constraints (Horizontal/Vertical, Coincident, Parallel, Perpendicular, Equal, Tangent, etc.) appear as badges in the canvas.
- Fully constrained sketches show black geometry; unconstrained is blue.
- Geometry is drawn on a selected plane; "Look At" orients the view.

## Key Observations from Onshape
- Sketch toolbar with tools for Line, Rectangle, Circle, Arc, Point, etc.
- Automatic inferencing while sketching (coincident, horizontal, etc.).
- Dimension tool (shortcut D); can enter numbers or variables (#param).
- Color coding: blue = under-defined (draggable), black = fully defined, red = over-defined.
- Constraints and dimensions are first-class; rectangle tool creates lines + coincident/parallel/perpendicular/horizontal constraints.
- Sketch must be on a plane; complete with checkmark.

## Implications for PyModeler stub
- Start with a table/list-based editor (not full canvas) for reliability and schema fidelity.
- Allow adding point/line/circle/arc entities and length/radius dimensions.
- Show entities, constraints, and dimensions in separate views.
- Connect directly to the existing Sketch data model (which already validates against JSON Schema).
- Later increments can add a 2D canvas with mouse drawing, snapping, and visual constraint badges.
- Integrate with FeatureHistory so a sketch can be selected and extruded.

Research complete. Proceeding to table-based SketchEditorWidget implementation.
