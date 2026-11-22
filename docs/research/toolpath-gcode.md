# Toolpath / G-code Generation Research

## Sources
- Basic rectangular pocket and contour G-code patterns from public CNC programming references (cncprogramminghub.com, edufacturing.com, hel mancnc.com, etc.).
- Standard G-code: G00 rapid, G01 linear feed, G17 XY plane, G21 metric, G90 absolute, G54 work offset, M03 spindle, M05 stop, M30 end.
- Typical parameters: tool diameter, stepover (50-70% of diameter), depth of cut (multiple passes), feed rates, safe Z height, plunge feed.

## Key Concepts for Early Stub
1. **Rectangular Pocket**: Clear material inside a rectangle.
   - Offset tool path inward by tool radius from walls.
   - Multiple depth passes (Z levels).
   - Roughing: zig-zag, spiral outward, or concentric rectangles.
   - Finish pass along the final contour.
2. **Contour / Profile**: Follow an outer or inner boundary.
   - Tool center offset by radius (climb or conventional).
   - Multiple depth passes.
3. **Simple Linear Moves**: For a stub, generate sequences of G00 (rapid to XY, safe Z) + G01 (plunge then cut path) + retract.
4. **Safety**: Always start with safe Z above stock, end with retract + program end.
5. **Parameters to expose**: width, height, depth, tool_diameter, stepover_fraction, depth_of_cut, feed, plunge_feed, safe_z, origin offset.

## Mozaik / Fusion / Onshape Inspiration
- Fusion 360: 2D Pocket, 2D Contour strategies with stepdown, stepover, lead-in/out (deferred).
- Mozaik: CNC-ready outputs from nested sheets, but focus on panel cutting; toolpaths are more specialized.
- Early PyModeler stub: pure-Python generator for rectangular pocket and simple closed-contour profile that emits readable G-code text. No geometry kernel dependency. Schema-validated input + generated program string.

## Next Implementation Steps (this run)
- JSON Schema for ToolpathJob (operation type, dimensions, tool, feeds, generated gcode).
- Pure-Python class that can pack a rectangular pocket (concentric or simple zig-zag) and a contour, emitting G-code.
- Tests for schema, generation, and basic output content.
- No UI yet (property panel later).

Last researched: 2026-11-21
