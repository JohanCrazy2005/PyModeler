# Constraint Visual Feedback Research

## Fusion 360
- Small constraint icons (glyphs) appear next to constrained entities when "Show Constraints" is enabled in the Sketch Palette.
- Icons include specific symbols for horizontal, vertical, coincident, tangent, equal, parallel, perpendicular, etc.
- Entity colors indicate status:
  - Blue: under-constrained
  - Black: fully constrained
  - Green: fixed
  - Purple: projected
  - Red: over-constrained or failed
- Hover over a constraint icon highlights related entities.
- Fully constrained sketches show a lock icon in the browser.

## Onshape
- Constraint icons appear on hover over entities or when "Show constraints" is enabled.
- Colors:
  - Blue: under-constrained
  - Black: fully constrained
  - Red: problem/over-constrained
- Constraint icon colors: black-on-gray for well-defined, white-on-red for problems.
- Hover highlights related entities.
- Constraint Manager panel lists all constraints with filtering and status.

## Implementation Notes for PyModeler
- Start with simple colored markers / text labels near entities (no full solver yet).
- Place badges at midpoints of lines or near centers of circles/arcs/points.
- Tooltip on badge shows constraint type and involved entity IDs.
- **Done (2026-11-27)**: basic text badges (H/V/C/= etc., type:value) implemented in SketchCanvasWidget._draw_badges.
- Later: proper glyph icons, full DOF analysis for under/fully/over status, and color entities accordingly.
- Toggle visibility of badges via a button or always-on for now.

Sources: Autodesk Fusion Help, Onshape Help, community forums.
