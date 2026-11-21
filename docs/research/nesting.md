# Nesting Concepts (Rectangular Packing Stub)

Research notes for Phase 4 simple nesting. Last updated: 2026-11-21.

## Mozaik Optimizer
- Dedicated Optimizer module driven from Cutlist Tab ("Optimize!" button).
- Places parts onto stock sheets maximizing yield.
- Supports rectangular and true-shape nesting.
- Key parameters: sheet size, trim/edge margin, part spacing (kerf / tool diameter + clearance), grain direction lock, flip-sheet sequencing, sequence-by-cabinet.
- Outputs: nested sheet patterns (visual), yield %, remnant management, labels, G-code.
- Quality levels (Estimate / Good / Better / Best) trade speed vs. search depth.
- Options: batch optimize multiple materials, optimize selected parts only.

## Fusion 360 / Onshape
- Nesting is less central (more CAM or separate Nesting workspace in some Autodesk products).
- Sheet-metal flat patterns are exported (DXF) for external nesting or laser/waterjet software.
- Onshape has some arrangement tools but not full production nesting like Mozaik.

## Rectangular vs True-Shape
- **Rectangular nesting**: treat every part as its axis-aligned bounding box. Fast, sufficient for panels, plates, rectangular blanks, and many wood/cabinet parts. Classic bin-packing (shelf, guillotine, maxrects).
- **True-shape nesting**: uses real polygon outlines (with holes, rotations at arbitrary angles). Higher yield for complex laser parts; more expensive computationally and requires contour geometry.
- For early PyModeler (panel / sheet-metal / cut-list focus) rectangular is the right first step.

## Typical Inputs / Outputs
**Inputs**
- Stock sheet dimensions (width × height)
- Kerf / part spacing
- Optional trim / edge margin
- List of parts: width, height, quantity, optional rotation allowed (grain lock), material
- Optional: multiple sheet sizes, remnant library

**Outputs**
- Number of sheets used
- Per-sheet layouts: list of placements (x, y, width, height, part reference, rotated?)
- Yield percentage (used part area / total sheet area)
- Remnants (optional later)

## Algorithm notes (stub)
- Simple shelf packing or maximal-rectangles approximation is enough for a first increment.
- Sort parts by descending height or area.
- Place left-to-right on current shelf; open new shelf or new sheet when needed.
- Respect kerf between parts and from edges.
- Optional 90° rotation when allowed and beneficial.
- No true-shape, no multi-sheet-size optimization, no genetic search yet.

## PyModeler design decisions (this increment)
- New schema-validated **NestingJob** capturing sheet size, kerf, parts, and computed layouts + yield.
- Pure-Python rectangular packer stub (shelf packing with optional rotation).
- Helper to seed a NestingJob from an existing CutList (using width × depth as the 2D blank).
- No UI, no G-code, no true-shape yet.
- Aligns with Mozaik-style manufacturing helpers already present (CutList, BOM, Materials).

## References
- Mozaik Optimizer guides and customer documentation
- Classic 2D bin-packing literature (shelf packing, MaxRects)
- Cutlist / nesting tools used in small-shop manufacturing
