# Timeline Rollback Marker and Feature Reordering

Research notes for implementing a Fusion 360 / Onshape-style feature timeline with a rollback marker and basic reordering support. Data model first.

## Sources

- Autodesk Fusion 360 Help: Use the Timeline  
  https://help.autodesk.com/view/fusion360/ENU/?contextId=LP-STEPS-P13N-SNP-GS-OTH-CRD-2
- Onshape Help: Feature and Part Lists (rollback bar section)  
  https://cad.onshape.com/help/Content/feature_list.htm
- Onshape video / documentation summaries on rollback bar and feature reorder

## Fusion 360 Timeline

- Features appear in chronological order in the Timeline.
- A **Timeline Marker** (slider) can be dragged to any point.
- Features after the marker are temporarily suppressed; the model shows the state up to the marker.
- Buttons: Play, Move to Beginning, Move to End, Previous/Next Step.
- Features can be dragged to reorder (when dependencies allow). Child features cannot be moved before their parents.
- Individual features can also be suppressed / unsuppressed independently of the marker.
- Editing a feature regenerates subsequent features.

## Onshape Feature List + Rollback Bar

- Features listed top-to-bottom (order of creation / regeneration).
- Thick **Rollback bar** at the bottom of the feature list by default.
- Dragging the rollback bar temporarily suppresses all features *below* it. The graphics area shows the model at that point.
- Right-click a feature → “Roll to here”.
- Right-click rollback bar → “Roll to end”.
- New features are inserted at the current rollback position.
- Features can be dragged to reorder. A child cannot be placed above a parent.
- Individual Suppress / Unsuppress from context menu (distinct from rollback).
- Folders can group features; suppressing a folder suppresses its contents.
- Regeneration is sequential from top to bottom; only features up to the rollback bar are computed.

## Design Implications for PyModeler

1. **Rollback marker is a position index** (or “after feature N”) stored on the FeatureHistory.
   - `rollback_marker`: integer, number of leading features that are active (0 … len(features)).  
     `None` or `len(features)` means “at end – all features active”.
2. **Recompute only features up to the marker.**  
   Features after the marker are skipped in `recompute_meshes` (treated as temporarily suppressed).
3. **Explicit suppress flag** (optional, for later) can be added per-feature; for this increment the marker is sufficient.
4. **Reordering** is a pure data-model operation: move an item in the `features` list, then recompute.  
   Dependency checking (parent/child) is deferred; for now any reorder is allowed and the user is responsible for validity.
5. New features are appended (or inserted at marker) so the marker can stay at the end by default.
6. Schema must remain the source of truth; marker is an optional integer property on FeatureHistory.

## Next Implementation Steps (this run)

- Add `rollback_marker` (optional integer) to `feature_history.schema.json`.
- Extend `FeatureHistory` with `set_rollback()`, `get_active_features()`, `reorder()`.
- Make `recompute_meshes` respect the marker.
- Tests for marker suppression and reordering.
- Living docs updated.

Later: UI drag of marker, visual indicator in feature tree, dependency-aware reorder, explicit per-feature suppress.
