# Hole Feature

Research notes for the Hole feature in Fusion 360, Onshape, and manufacturing-oriented tools.

## Fusion 360

- Dedicated **Hole** tool under Design > Solid > Create > Hole.
- Placement: At Point (single), From Sketch (multiple points), or on faces/edges.
- Hole types: Simple, Counterbore, Countersink.
- Tap types: Simple, Clearance, Tapped (with thread library), Taper Tapped.
- Extents: Distance (blind), To, All (through).
- Parameters: diameter, depth, counterbore diameter/depth, countersink angle/diameter, thread size/design.
- Supports parametric values and references.
- Generates recognized hole semantics useful for drawings (hole callouts), CAM, and manufacturing.
- Preferable to sketching circles + Cut-Extrude because it packages geometry + fastener data into one editable feature.

Sources: Autodesk Fusion Help – Create a hole, Hole tool tutorials.

## Onshape

- Hole feature creates simple, counterbore, or countersink holes.
- Placement via sketch points or mate connectors.
- Termination: Blind (depth), Through All, Up to Next, Up to Entity.
- Hole types include Drilled, Clearance, Tapped, PEM.
- Supports precision/tolerance controls that propagate to drawings.
- Can cut multiple parts in the merge scope.
- FeatureScript-based; parameters are strongly typed (lengths, enums).

Sources: Onshape Help – Hole, Feature UI documentation.

## Manufacturing relevance (Mozaik-inspired)

- Holes are first-class for joinery, hardware (shelf pins, fasteners), and CNC toolpaths.
- Having a dedicated Hole feature (instead of pure extrude-cut) enables:
  - Automatic hole callouts / tables.
  - Standard fastener sizing.
  - Future G-code / drilling cycles.
  - Cut-list / BOM annotations for hardware.

## Implications for PyModeler

Current mesh-based approach:

1. Schema for HoleFeature with diameter, depth, center position (or sketch point reference), operation="cut".
2. Basic mesh generation: produce a cylinder tool body of the given diameter/depth.
3. **Done**: integrate with mesh Boolean (cut) against the target solid in Part.recompute.
4. Next: support counterbore/countersink, sketch-point placement, through-all, and thread stubs.

This is the first Phase 4 feature and aligns with the design-to-manufacture goal.
