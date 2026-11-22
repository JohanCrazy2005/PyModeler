# Expression Functions & Unit Helpers – Research Notes

## Fusion 360 / Onshape
- Both support rich parameter expressions with arithmetic, parentheses, and mathematical functions.
- Trigonometric functions (`sin`, `cos`, `tan`, and inverses) typically take **degrees** by default (CAD convention). Explicit radians are available via unit suffixes or dedicated forms.
- Common functions: `sqrt`, `abs`, `min`/`max`, `floor`/`ceil`/`round`, `exp`, `log`, `hypot`, power (`^` or `**`).
- Constants: `pi`, `e`.
- Unit-aware: expressions can mix units of the same type (e.g. `3 in + 10 mm`); result must be unitless or first-power unit. Conversion helpers and unit suffixes are first-class.
- Onshape evaluates via FeatureScript; Fusion via its parameter engine. Both propagate changes immediately.

## FreeCAD
- Expressions support operators, functions (`sin`/`cos` in degrees by default, `sqrt`, etc.), constants (`pi`, `e`), and unit suffixes.
- Access to a subset of the Python `math` module via `_math`.

## PyModeler implementation notes
- Extended `ParameterStore.evaluate_expression` (and parameter expressions) with:
  - `**` / power operator
  - Safe function set: `sin`/`cos`/`tan` (degrees), `asin`/`acos`/`atan`/`atan2` (degrees), `sqrt`, `abs`, `min`/`max`, `floor`/`ceil`/`round`, `exp`, `log`/`log10`, `hypot`, `pow`
  - Explicit radians versions: `sin_rad`, `cos_rad`, `tan_rad`
  - Constants: `pi`, `e`
  - Simple numeric unit helpers: `in_to_mm`, `mm_to_in`, `deg_to_rad`, `rad_to_deg`
- All evaluation remains pure Python (`ast` + `math`), no external expression libraries.
- Dimension values in the constraint solver automatically benefit from the richer expressions.
- Future: full unit system with suffixes, more functions, conditional expressions.

Last updated: 2026-11-22 (trig / unit-aware functions)
