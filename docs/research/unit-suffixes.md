# Research: Unit Suffixes in Expressions (Fusion 360, Onshape)

## Fusion 360
- Expressions in User Parameters and dimensions support explicit unit suffixes, e.g. `"6.25 in"`, `"10 mm"`, `"2.5 cm"`.
- The suffix overrides the document default units. Bare numbers use the document unit.
- Mixing units of the same type is allowed and converted (e.g. `2 in + 10 mm`).
- Result is always stored/displayed in the document base unit (typically mm or in depending on settings).
- Unit helpers and full dimensional analysis exist; invalid unit combinations (length + angle, area into length) are rejected.

## Onshape
- Numeric fields and Variable expressions accept unit keywords: `mm`, `in`, `inch`, `inches`, `cm`, `m`, `ft`, `deg`, etc.
- Plurals allowed. Expressions must evaluate to a value with units to the first power (or unitless).
- Examples: `3in + 2.5mm`, `sqrt(16)m`, `cos(30deg)`.
- Bare numbers are unitless unless the field supplies a default unit; mixing length units is converted.
- FeatureScript-based evaluation handles unit conversion transparently.

## Implications for PyModeler
- Base length unit remains millimeters (consistent with existing `in_to_mm` helpers and toolpaths).
- Preprocess expressions to expand numeric literals followed by unit suffixes into pure numeric mm values before AST evaluation.
- Supported length suffixes (case-insensitive, optional space): `mm`, `cm`, `m`, `in`, `inch`, `inches`, `ft`, `foot`, `feet`.
- Angle suffixes (`deg`, `rad`) can be added later if needed; current trig already takes degrees.
- Keep the existing function helpers (`in_to_mm`, etc.) for explicit conversion.
- Invalid or unknown suffixes raise ParameterEvaluationError.
- This enables user-friendly inputs like `2 in + 10 mm` while keeping the internal model in mm.

Sources: Autodesk Fusion 360 Help (UserParameter.expression), Onshape Numeric Fields / FeatureScript docs, community examples.
Last updated: 2026-11-23
