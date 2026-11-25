# Dimension Export Research (DXF)

## Purpose
Export sketch dimensions as proper DXF DIMENSION entities so shop drawings and manufacturing hand-off include driving dimensions.

**Library**: ezdxf (already approved).

## Findings
- ezdxf supports `add_linear_dim`, `add_radius_dim`, `add_diameter_dim`, `add_angular_dim_2l`, `add_angular_dim_3p`, `add_angular_dim_cra`, etc.
- Must call `.render()` to generate the anonymous BLOCK containing the visual representation (required for AutoCAD compatibility).
- Use `setup=True` when creating the document so default dimstyles (EZDXF, EZ_RADIUS, EZ_CURVED) exist.
- Linear dimensions take `base` (location of dim line), `p1`, `p2`.
- Radius / diameter dimensions take `center`, `radius`, `angle` (EZ_RADIUS style).
- Angular dimensions: by 2 lines (`add_angular_dim_2l` with `base`, `line1`, `line2`), by 3 points, or by center/radius/angles (`add_angular_dim_cra`).

## Implementation
- Extended `export_sketch_to_dxf` with `include_dimensions=True` (default).
- New layer `DIMENSIONS`.
- Length/distance dimensions on lines become linear DIMENSION entities (offset ~5 units).
- Radius dimensions on circles/arcs become radius DIMENSION entities at 45°.
- Diameter dimensions on circles/arcs become diameter DIMENSION entities at 45° (dimtype 3).
- Angle dimensions between two lines become angular DIMENSION entities (2-line, dimtype 2) with a modest base offset.
- Failures are skipped for robustness (stub).

## Next
- Better placement (use dimension value or user offset / parameters).
- Angular by 3 points or arc-based when entities allow.
- Import of DIMENSION entities back into sketch dimensions (harder).

Last updated: 2026-11-25 (diameter + angular)
