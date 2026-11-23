# Nesting Research Notes

## Sources
- Mozaik Manufacturing Software: automatic nesting / optimization of rectangular parts onto sheet stock, with grain direction, remnant management, and yield reporting.
- Fusion 360 / Autodesk Fusion: Arrange and Nesting tools (rectangular and true-shape in some packages).
- Onshape: no native nesting; users typically export and use external CAM/nesting.
- Classic algorithms: shelf packing, guillotine, MaxRects for rectangular bin packing.

## Key Concepts for Early Stub
1. **Rectangular NestingJob**: Sheet size (width × height), kerf/spacing, optional trim margin, list of parts (width, height, quantity, can_rotate).
2. **Shelf Packer**: Simple pure-Python algorithm that places parts left-to-right on shelves, opening a new shelf or new sheet when needed. Optional 90° rotation.
3. **Yield**: Used area / sheet area, overall and per sheet.
4. **From CutList**: Helper that seeds a NestingJob from an existing CutList (width × depth as the 2D blank).
5. **Schema-driven**: Validated on construction and after packing.

## Mozaik Inspiration
- Automatic placement with user-controlled grain / rotation rules.
- Remnant tracking for later reuse.
- Yield and sheet-count reporting for shop planning.
- Later: true-shape, grain matching, multi-material.

## Next Implementation Steps (this run)
- JSON Schema for NestingJob.
- Pure-Python shelf packer + NestingJob class.
- Helper from CutList.
- Tests for packing, rotation, yield, and schema.
- No UI yet.

Last researched: 2026-11-21

## Update 2026-11-22
- Added per-sheet remnant_area tracking in NestingJob layouts (sheet_area - used_area).
- Summary now reports remnant. Schema already allows additional properties on layouts.
