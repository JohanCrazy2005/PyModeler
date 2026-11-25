# Dimension Export Research (DXF)

## Purpose
Export sketch dimensions as proper DXF DIMENSION entities so shop drawings and manufacturing hand-off include driving dimensions.

**Library**: ezdxf (already approved).

## Findings
- ezdxf supports `add_linear_dim`, `add_radius_dim`, `add_diameter_dim`, etc.
- Must call `.render()` to generate the anonymous BLOCK containing the visual representation (required for AutoCAD compatibility).
- Use `setup=True` when creating the document so default dimstyles (EZDXF, EZ_RADIUS) exist.
- Linear dimensions take `base` (location of dim line), `p1`, `p2`.
- Radius dimensions take `center`, `radius`, `angle`.

## Implementation
- Extended `export_sketch_to_dxf` with `include_dimensions=True` (default).
- New layer `DIMENSIONS`.
- Length/distance dimensions on lines become linear DIMENSION entities (offset ~5 units).
- Radius dimensions on circles/arcs become radius DIMENSION entities at 45°.
- Failures are skipped for robustness (stub).

## Next
- Diameter and angular dimensions.
- Better placement (use dimension value or user offset).
- Import of DIMENSION entities back into sketch dimensions (harder).

Last updated: 2026-11-25
