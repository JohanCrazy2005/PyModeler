# Manufacturing Drawings – Dimension Groups Research

## Purpose
Polish manufacturing drawing outputs and sketch dimension UX so ordinate dimensions can be managed as groups (shared datum, stacked leaders) and dimensions have exact, reliable association to geometry handles.

**Sources**: Fusion 360 Drawing workspace Ordinate Dimension docs, Onshape Drawing Ordinate Dimension (groups move together), Inventor Ordinate Set, AutoCAD DIMORD / OrdinateDimensionSets.

**Date**: 2026-11-27

## Key Findings

### Ordinate Dimension Groups
- **Fusion 360**: Place origin (0,0) then additional feature points. Leaders can be aligned via object tracking. Deleting origin deletes associated ordinates. ASME vs ISO text placement differs.
- **Onshape**: Ordinate dimensions created as a group move together when one is moved. Groups share a logical group identity. Styles apply per dimension or group.
- **Inventor**: Ordinate Set tool selects multiple geometry, places as a set with shared origin options (positive both directions, show direction arrow, reverse).
- **AutoCAD**: Ordinate dimensions reference a UCS origin; sets can be created programmatically via OrdinateDimensionSets.Add.

Common pattern:
- Shared origin / datum point.
- Axis-aligned (X or Y) leaders that stack.
- Group identity so moving one (or the origin) moves the set.
- Optional leader styles (straight / jogged / none).

### Exact Handle Association
- Dimensions must reference precise entity handles (point id, line id, arc center, etc.) rather than nearest-match heuristics.
- On import, prefer exact entity recovery when definition points match existing geometry within tight tolerance; fall back to creation only when necessary.
- UI should show the associated entities clearly and allow re-association.

## Implementation Plan for PyModeler
1. UI button in Sketch Editor: "Add Ordinate Group" – select ≥2 points, choose axis / origin / offset / leader style, call existing `add_ordinate_group`.
2. Dimensions table: sort/group by `group_id`, highlight shared groups, show group column prominently.
3. Canvas: (future) group badges or drag-group behavior.
4. DXF export already stamps group_id; ensure leaders respect style.
5. Exact association: strengthen import matching (tighter tol + prefer existing entities) and store entity ids explicitly.

This is a small, complete increment focused on the UI grouping entry point and table polish.

Last updated: 2026-11-27
