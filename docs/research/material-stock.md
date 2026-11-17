# Material / Stock Definitions

Research notes for Phase 2 manufacturing helpers. Sources: Mozaik material libraries, Fusion 360 material appearance / physical materials, Onshape material assignments, general cabinet/furniture CAD practices. Last updated: 2026-11-17.

## Fusion 360 / Autodesk Fusion
- Physical Materials and Appearance libraries.
- Materials can be assigned to bodies or components.
- Include density, thermal, etc. for simulation later.
- Appearance is visual; physical is for mass/properties.

## Onshape
- Materials can be assigned at the part or body level.
- Custom material libraries possible.
- Used for mass properties and BOM.

## Mozaik / manufacturing-focused tools
- Strong material / stock library is central.
- Sheet materials: thickness, type (plywood, MDF, particleboard, solid), cost per sheet or unit, grain direction, edge banding options, finish.
- Filtering cut lists by material.
- Stock definitions drive cut sizes, nesting, and hardware compatibility.
- Part library can override or add manufacturing metadata.

## PyModeler design decisions (this increment)
- Simple `MaterialStore` (schema-driven) holding named materials with:
  - name (unique)
  - thickness (for sheet stock)
  - type (plywood, mdf, solid_wood, aluminum, …)
  - unit
  - optional density, cost, grain_direction, comment, metadata
- Parts already accept an optional `material` (string name or object). Next steps can resolve the string against a store.
- No UI yet — pure data + tests. Enables cut-list generation later.
- Keep lightweight; expand when cut lists and BOM land.

## Next after this
- Cut-list stub that walks Parts and looks up material thickness / type.
- Optional UI property panel to assign material from store.
- BOM generation.

Last updated: 2026-11-17
