# DXF Additional Entities Import (SPLINE / ELLIPSE / TEXT)

## Purpose
Extend `import_dxf_to_sketch` beyond LINE/CIRCLE/ARC/LWPOLYLINE/POLYLINE to support common manufacturing/CNC DXF entities:

- **SPLINE**: B-spline / NURBS curves (common for freeform profiles)
- **ELLIPSE**: elliptical arcs (often from projected circles or true ellipses)
- **TEXT**: single-line text (stub; useful for notes/labels on drawings)

## Research Findings (ezdxf 1.4.x)

- **Path abstraction** (`ezdxf.path.make_path`): Converts SPLINE, ELLIPSE, CIRCLE, ARC, etc. into a unified Path of lines + cubic Bézier curves.
- **Flattening**: `path.flattening(distance=tol)` produces adaptive polyline approximation with maximum deviation `tol`. Suitable for manufacturing tolerance (e.g. 0.05–0.2 mm).
- **SPLINE**: `entity.flattening(distance)` or via Path. Control/fit points available but polyline approximation is safer for sketch import.
- **ELLIPSE**: Native `flattening(distance)` or Path. Full ellipses close; partial arcs possible. Not converted to true arcs unless circular (major==minor).
- **TEXT**: `dxf.text`, `dxf.insert`, `dxf.height`, `dxf.rotation`. Sketch schema has no text entity type, so store as point + metadata note.

## Implementation Decisions
- Approximate SPLINE and ELLIPSE as connected LINE entities (polyline) using `flattening(distance=0.1)`.
- TEXT becomes a point at insert location; text content stored in sketch.metadata["imported_texts"] as list of {text, x, y, height, rotation}.
- Keep existing virtual_entities path for polylines (bulge → ARC).
- Tolerance is fixed for now; future: user-configurable or adaptive to entity size.

## References
- ezdxf path: https://ezdxf.mozman.at/docs/path.html
- ezdxf SPLINE: https://ezdxf.mozman.at/docs/dxfentities/spline.html
- ezdxf ELLIPSE: https://ezdxf.mozman.at/docs/dxfentities/ellipse.html
- ezdxf TEXT: https://ezdxf.mozman.at/docs/dxfentities/text.html

Last updated: 2026-11-24
