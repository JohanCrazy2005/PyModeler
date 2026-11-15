# Research: User Parameters / Variables (Fusion 360, Onshape, Mozaik)

## Fusion 360
- **User Parameters**: Explicitly created in the Change Parameters dialog (Modify > Change Parameters). Fields: Name, Unit, Expression, Comment.
- **Model Parameters**: Auto-generated from sketch dimensions and features; can also be created on-the-fly by typing `name=value` in a dimension field.
- Both can be referenced by name in any sketch dimension or feature input.
- Expressions support arithmetic (+ - * /), parentheses, functions (sin, etc.), unit conversions, and references to other parameters.
- Changing a user parameter propagates immediately to all dependent geometry.
- Favorite / global parameters for cross-document reuse.

## Onshape
- **Variables** are first-class features in the Part Studio feature tree (or managed via Variable Studio / Variable Table).
- Types: Length, Angle, Number, Any.
- Created via toolbar or on-the-fly with `#` (hash) prefix in dimension inputs.
- Can be used in expressions that reference other variables (`#width * 2`).
- Configuration Variables allow families of designs driven by the same variables.
- Variables must appear above features that reference them in the feature tree (or be in Variable Studio).

## Mozaik
- Job-level and product-level **Parameters** control construction rules (rail widths, reveals, joinery, shelf clearances, etc.).
- User-created named parameters (e.g., BTH = base toe height) can drive point coordinates and formulas in side-shape editors and other calculated fields.
- Reserved parameters (H = height, D = depth, part thickness, opening sizes) are always available.
- Formulas can reference library, system, reserved, and user parameters; changes rebuild affected geometry and cut lists.

## Implications for PyModeler
- Introduce a `ParameterStore` of named user parameters (name, value or expression, optional unit).
- Sketch dimensions (and later features) already support string values as parameter names; the store will resolve them.
- Simple expression evaluation (numeric literals + named references + basic arithmetic) is sufficient for the first increment.
- Schema-driven so parameters are versionable and serializable with the design.
- Later: model parameters auto-created from dimensions, full expression engine, units handling, and UI Parameter table.

Sources consulted: Autodesk Fusion Help, Onshape documentation/blogs, Mozaik support articles and user guides (2025–2026).
