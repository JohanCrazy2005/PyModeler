# Lightweight 2D Constraint Solver Stub – Research Notes

## Fusion 360 / Onshape
- Both use **variational geometric constraint solvers**.
- Constraints (horizontal, vertical, equal, parallel, perpendicular, coincident, tangent, etc.) and driving dimensions are turned into a system of nonlinear equations.
- The solver adjusts free point coordinates (and radii, angles) to minimize residuals while preferring solutions close to the current geometry (least-movement principle).
- Fully constrained sketches have zero remaining degrees of freedom; under-constrained stay blue, over-constrained turn red.
- Real-time feedback during dragging.

## FreeCAD PlaneGCS
- Open-source reference implementation (used by FreeCAD Sketcher).
- Numeric methods: DogLeg, Levenberg-Marquardt, BFGS, SQP.
- Supports points, lines, circles, arcs + full set of constraints.
- Python bindings available (planegcs package).

## Lightweight Python approaches
- scipy.optimize.least_squares (or minimize) is the standard pure-Python starting point.
- Residuals:
  - Horizontal line: dy = 0
  - Vertical line: dx = 0
  - Equal length: |len_a - len_b| = 0
  - Coincident points: dx = 0, dy = 0
  - Parallel: cross product of direction vectors = 0
  - Perpendicular: dot product = 0
- Fixed points are removed from the free variable vector.
- Driving dimensions become equality residuals (or soft with high weight).

## PyModeler stub plan
- Pure scipy + numpy implementation (no C++ dependency).
- Handles the most common constraints already present in the schema: horizontal, vertical, equal, coincident, parallel, perpendicular, fixed.
- Method `Sketch.solve(max_nfev=100, parameters=None)` that updates point coordinates in-place.
- Returns success flag + residual norm.
- Driving dimensions (numeric values or string ParameterStore refs) as hard residuals: length, distance, radius, diameter, angle (two lines, degrees).
- Free radii of circles/arcs are variables (bounded >= 0).
- Parameter evaluation: string dimension values resolved via ParameterStore.evaluate (bare names); unresolved skipped.
- Later: full expression evaluation in dimension values, tangent, better under/over detection, Jacobian sparsity, arc angles as free variables.

This keeps the main branch pure Python + public libs and gives a concrete foundation for further constraint propagation after transforms.

Last updated: 2026-11-22 (parameter evaluation for dimension values)