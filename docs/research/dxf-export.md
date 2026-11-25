# DXF Export (ezdxf)

## Purpose
Export 2D sketch geometry and closed profiles to DXF for:
- Shop drawings / dimensioned outputs
- CNC / manufacturing hand-off
- Interoperability with other CAD/CAM tools

**Library**: **ezdxf** (already approved and listed in requirements).

## Implementation Notes (stub)
- `src/pymodeler/io/dxf.py`
- `export_sketch_to_dxf(sketch, path)` writes:
  - Non-construction LINE, CIRCLE, ARC entities on layer `SKETCH`
  - Closed profiles (from `extract_simple_profiles`) as closed LWPOLYLINE or CIRCLE on layer `PROFILES`
- `export_profiles_to_dxf(profiles, path)` for already-extracted profile lists.
- DXF version R2010 (widely compatible).
- Construction geometry is skipped.
- No dimension entities yet (future: add DIMENSION entities driven by sketch dimensions).

## Future Enhancements
- Full dimensioned drawings (linear, radial, angular dimensions from sketch dimensions).
- Multi-sketch / part-level export (projected views later).
- Import of DXF into sketches (basic LINE/CIRCLE/ARC + LWPOLYLINE closed/open profiles as sequential lines).
- Layer conventions matching common manufacturing workflows.
- Export of cut-list related outlines.

## References
- ezdxf documentation: https://ezdxf.readthedocs.io/
- DXF is a standard 2D interchange format used by virtually all CAD/CAM packages.

Last updated: 2026-11-24 (LWPOLYLINE import added)

## Import Improvements (2026-11-24)

- `import_dxf_to_sketch` now supports both `LWPOLYLINE` and legacy `POLYLINE`.
- Bulge values are no longer flattened to straight segments. `virtual_entities()` expands them into proper `ARC` entities (plus `LINE` for zero-bulge segments). Closed flags are respected automatically.
- Research: ezdxf `virtual_entities()` and `bulge_to_arc` (angles in radians → degrees for Sketch). Keeps the importer simple while gaining curved geometry fidelity for manufacturing hand-off.
