# Sketch Degrees-of-Freedom (DOF) Analysis Research

## Fusion 360
- Sketch geometry color indicates constraint status:
  - Blue: under-constrained (still has degrees of freedom; can be dragged)
  - Black: fully constrained (size and position completely defined)
  - Red: over-constrained or failed
  - Green: fixed / locked
- Fully constrained sketches show a lock icon in the browser.
- A point has 2 DOF; a line has DOF from its endpoints (4) plus orientation/length, reduced by constraints and dimensions.
- Good practice is to fully constrain sketches before creating solid features.

## Onshape
- Blue: under-constrained
- Black: fully constrained
- Red: over-constrained / problem
- Status is computed by the constraint solver and shown in real time.
- Constraint Manager lists constraints with status.

## Implementation Notes for PyModeler (stub)
- Implement a simple DOF counting heuristic (not a full geometric solver yet):
  - Free point: 2 DOF
  - Fixed point: 0 DOF
  - Circle / Arc radius: +1 DOF (unless dimensioned)
  - Geometric constraints remove approximate DOF (horizontal/vertical/equal/parallel/perpendicular: 1; coincident: 2; fixed: 2)
  - Driving dimensions remove 1 DOF each
- Sketch is considered fully constrained when remaining DOF <= 0.
- Entity-level status:
  - "fully" if the entity (or its defining points) participates in enough locking constraints/dimensions or the whole sketch is fully constrained
  - "under" otherwise
  - "over" if remaining DOF < 0 (heuristic)
- Use status to color entities on the sketch canvas: blue for under, black for fully.
- Later: integrate a real 2D constraint solver (e.g. via scipy or a dedicated library) for accurate status and solving.

Sources: Autodesk Fusion Help (Fully define and constrain sketches), Onshape Help, community discussions.
