# Parametric Transform Intent

## Research (Fusion 360 / Onshape)

In Fusion 360 and Onshape, free "Move" or gizmo transforms on parametric geometry are usually either:

- Captured as a timeline feature (Move/Copy, Move Face) that remains editable, or
- Rejected / converted into parameter or sketch edits when the geometry is fully constrained.

Direct mesh transforms that ignore the feature history break the parametric model. Preferred workflow:

1. User drags a gizmo on a body generated from a sketch + features.
2. The system attempts to update the driving sketch (plane origin, free points, or driving dimensions) by the delta.
3. The feature tree is recomputed, producing the new geometry at the updated location with identity transform.
4. If the sketch is fully constrained or the change cannot be applied cleanly, the free transform is kept (or a warning is shown).

Onshape's Move Face is a direct-editing tool mainly for imported solids; for native parametric parts the preferred path is still editing the driving sketch or parameters.

## Implementation in PyModeler (this increment)

- Pure helper `apply_translation_to_sketch` / `apply_translation_to_part_sketches` offsets the sketch plane origin and free point entities.
- Viewport `transform_committed` signal is now handled in MainWindow: a translation delta on the current part is applied to its sketches, then the part is recomputed (body reappears at identity).
- Scale/rotate intent and full constraint-aware solving are future work.
- Headless-safe; no OpenGL required for the helper.

Last updated: 2026-11-19
