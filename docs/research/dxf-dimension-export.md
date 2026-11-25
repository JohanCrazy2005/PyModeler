# Dimension Export Research (DXF)

## Purpose
Export sketch dimensions as proper DXF DIMENSION entities so shop drawings and manufacturing hand-off include driving dimensions.

**Library**: ezdxf (already approved).

## Findings
- ezdxf supports `add_linear_dim`, `add_aligned_dim`, `add_radius_dim`, `add_diameter_dim`, `add_angular_dim_2l`, `add_ordinate_x_dim` / `add_ordinate_y_dim`, etc.
- Must call `.render()` to generate the anonymous BLOCK containing the visual representation (required for AutoCAD compatibility).
- Use `setup=True` when creating the document so default dimstyles (EZDXF, EZ_RADIUS, EZ_CURVED) exist.
- Linear dimensions take `base` (location of dim line), `p1`, `p2`.
- Aligned dimensions take `p1`, `p2`, `distance` (orthogonal offset of the parallel dim line).
- Radius / diameter dimensions take `center`, `radius`, `angle`.
- Angular (2-line) dimensions take `base`, `line1=(p1,p2)`, `line2=(p3,p4)`.
- Ordinate dimensions take `feature_location`, `offset` (leader end relative), `origin` (datum).

## Implementation
- Extended `export_sketch_to_dxf` with `include_dimensions=True` (default).
- New layer `DIMENSIONS`.
- Length/distance dimensions on lines become linear DIMENSION entities (offset ~5 units).
- Aligned dimensions on lines become aligned DIMENSION entities.
- Radius dimensions on circles/arcs become radius DIMENSION entities at 45°.
- Diameter dimensions on circles/arcs become diameter DIMENSION entities at 30°.
- Angle dimensions between two lines become angular DIMENSION entities (EZ_CURVED style).
- Ordinate dimensions on points become ordinate_x / ordinate_y DIMENSION entities.
- Failures are skipped for robustness (stub).
- Sketch helpers: `add_diameter_dimension`, `add_angle_dimension`, `add_aligned_dimension`, `add_ordinate_dimension`.
- Schema enum extended with "aligned" and "ordinate".

## Next
- Better placement (use dimension value or user offset / leader side) — partially done.
- Import of DIMENSION entities back into sketch dimensions (harder).
- Further ordinate group handling / multi-feature sets.

Last updated: 2026-11-25 (ordinate + aligned)
