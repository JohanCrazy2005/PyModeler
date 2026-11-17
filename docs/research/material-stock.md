# Material / Stock Definitions

Research notes for Phase 2 manufacturing helpers. Last updated: 2026-11-17.

## Fusion 360 / Autodesk Fusion
- Physical Materials (density, strength, thermal) separate from Appearance (visual).
- Materials assigned to bodies/components; used for mass properties and simulation.
- Limited built-in stock/sheet size concept; more emphasis on physical properties.

## Onshape
- Material libraries with density and appearance.
- Assigned per Part; mass properties computed from volume × density.
- Configurations can swap materials.

## Mozaik (manufacturing focus)
- Material / stock library is central: thickness, sheet size, grain, edge banding, CNC eligibility.
- Cut lists filter and group by material.
- Stock definitions drive nesting and material requirements.
- Part library entries carry material, thickness, and manufacturing metadata.

## PyModeler design decisions (this increment)
- `MaterialStore` – schema-validated library of material definitions.
- Each material supports:
  - name, category (wood/metal/plastic/composite/other)
  - type (sheet / solid / linear / other)
  - thickness, width, length (stock dimensions)
  - density, color, grain flag, unit, optional cost
- Part already accepts `material` as string (name/id) or object; no breaking change.
- Starter library via `create_default_library()` for common panel materials.
- Next consumers: cut-list generator (walk Parts → quantity, size, material) and light UI property panel.

## References
- Mozaik Cutlist / Part Library docs
- Fusion Physical Materials
- Onshape material assignment
