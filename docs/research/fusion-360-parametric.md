# Fusion 360 Parametric Modeling, Sketches, and Feature Workflow

Research notes for PyModeler. Sources: Autodesk Fusion help, tutorials (Maker Letters, CADArtifex, Product Design Online), and general parametric CAD practices. Last updated: 2026-11-15.

## Core Philosophy
Fusion 360 (now Autodesk Fusion) is a **history-based parametric CAD** system. Design intent is captured through:
- Sketches with geometric constraints and driving dimensions
- Features that consume sketches or other geometry
- A Timeline (feature history) that can be edited and recomputed
- User Parameters that drive dimensions across the design

Parametric modeling is preferred for engineering/manufacturing work because changes to early dimensions propagate correctly. Direct modeling (push/pull without history) is available for quick edits or imported geometry and can coexist.

## Sketch Workflow
1. Create Sketch on a plane (origin planes, construction planes, or planar faces).
2. Draw geometry: lines, rectangles, circles, arcs, splines, etc.
3. Apply geometric constraints (relationships, not numbers):
   - Horizontal / Vertical
   - Coincident
   - Tangent
   - Equal
   - Parallel / Perpendicular
   - Fix / Unfix
   - Midpoint
   - Concentric
   - Collinear
   - Symmetry
   - Curvature (G2 continuity)
4. Add driving dimensions (numerical or parameter-driven). Dimensions can be driven by User Parameters or equations.
5. Goal: Fully constrained sketch (geometry turns black; 0 degrees of freedom remaining). Under-constrained geometry is blue.
6. Finish sketch → use profile for features.

Best practices:
- Start from origin when possible.
- Use construction geometry for references.
- Fully constrain before creating features for predictable updates.
- Project existing geometry for associations.

## Parameters
- User Parameters (Modify → Change Parameters) act as the source of truth.
- Sketch dimensions and feature inputs can reference parameter names (e.g., `Width`, `Thickness`).
- Changing a parameter rebuilds the model.

## Feature Workflow & Timeline
- Base feature usually Extrude or Revolve from a sketch profile.
- Subsequent features: Extrude (join/cut/intersect), Revolve, Sweep, Loft, Fillet, Chamfer, Shell, Hole, Pattern, Mirror, etc.
- Timeline records every operation in order.
- Editing an early feature or dimension triggers recompute of all downstream features.
- Feature suppression, reorder (with care), and rollback are supported.
- Browser shows sketches, bodies, components, and construction geometry.

## Key Takeaways for PyModeler
- Sketch data model must store entities, constraints, and dimensions (with parameter references).
- Fully constrained sketches should be the recommended (and eventually enforced) path.
- Feature history / timeline is essential; features must store their inputs (sketch refs, parameters, options).
- Parameters / variables system should exist early so dimensions are not hard-coded.
- Support both parametric history and occasional direct edits without breaking the model.
- Extrude (and later Revolve) as the first solid features from sketches.

## References
- Autodesk Fusion Help: Sketches, Constraints
- Parametric vs Direct Modeling guides
- Common tutorial patterns for constrained mechanical parts
