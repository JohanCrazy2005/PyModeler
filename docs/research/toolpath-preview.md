# Toolpath / G-code Preview

## Context
Early rectangular toolpath generator already exists (pocket/contour, concentric/zigzag/spiral, lead-in/out, corner radius).  
Users need a quick way to inspect the generated G-code and visualize the 2D path without an external CAM viewer.

## Approaches in other tools
- Fusion 360 / Autodesk Fusion: Toolpath simulation with 3D stock + tool animation; 2D path overlay in the viewport.
- Onshape: Manufacturing workspace with toolpath preview (still maturing).
- Mozaik / cabinet tools: Nesting-centric; CNC output is often post-processed G-code or specialized formats; limited interactive path preview inside the design app.
- Simple Python CAM stubs (e.g. community scripts): Parse G-code and draw polylines with matplotlib or QPainter.

## Decision for this increment
- Schema-driven ToolpathJob already produces G-code.
- Add a pure-PyQt6 dialog:
  - Read-only monospace QPlainTextEdit for the full G-code.
  - QPainter widget that parses G00/G01/G03 lines, extracts XY points, and draws the tool-center path (arcs approximated as lines for preview).
  - Nominal rectangle outline shown dashed.
- Wired to Manufacturing menu as “Toolpath Preview…” with a sample pocket (easy to later bind to real part geometry).
- No new dependencies; headless-safe (paint path tested without display where possible).

## Next possible steps
- Bind toolpath generation to selected part / sketch bounding box.
- Better arc approximation (sample points along G02/G03).
- Z-level coloring or depth bands.
- Export G-code to file from the dialog.
