# Viewport Edge / Face Picking

Research notes for interactive selection of edges and faces in the 3D viewport (for Fillet, Chamfer, Shell, and future features).

## How commercial tools do it

### Fusion 360
- Selection priority filters: Body / Face / Edge / Component. Once a priority is set, clicks and box selections only hit that entity type.
- Click selects the nearest entity under the cursor; Ctrl/Shift for additive selection.
- Window (left-to-right) vs crossing (right-to-left) box select.
- Paint selection mode for dragging across entities.
- Pre-selection and filters keep the feature dialog from receiving the wrong topology type.

### Onshape
- Click toggles selection; additive by default in many contexts.
- “Create Selection” rules: tangent-connected faces/edges, loop/chain connected edges, protrusion/pocket, equal length, etc.
- Window select (enclosed vs crossing).
- “Select other” (tilde) cycles through entities along the ray when the desired one is occluded.
- Feature dialogs often expose a selection filter so only edges or only faces are accepted.

### Common patterns useful for PyModeler
1. Explicit mode or filter: Object / Edge / Face (keyboard or menu).
2. Click-to-pick nearest entity along the view ray, with a distance tolerance for edges.
3. Highlight the chosen edge or face.
4. Feed the indices (or stable IDs later) directly into the active feature’s edges/faces property.
5. Later: box select, “select other”, tangent/loop rules, persistent selection sets.

## Incremental plan for PyModeler
- Pure, headless-testable ray–edge and ray–face nearest-hit helpers (already useful for unit tests).
- Viewport selection mode (`object` | `edge` | `face`) switched by keys or menu.
- On click in edge/face mode, compute world ray, transform into the selected object’s local space, return nearest edge index or face index.
- Store the result and expose a simple string (comma-separated indices) that the property panel can consume.
- Property panel “Use Viewport Selection” button (or live update) copies the current viewport entity selection into the Edges/Faces field of Fillet/Chamfer/Shell.
- Keep the existing text-entry path; viewport picking is an additional, faster way.

This stays mesh-index based for now (same as the current property-panel text field). Stable topological IDs can come later.


## Polish increment (2026-11-24)
- Multi-select: Shift+click appends to edge/face selection (unique).
- Highlight: selected edges and face boundaries drawn in bright green overlay.
- Basic box select: drag in edge/face mode; entities whose projected center falls inside the screen rect are selected (additive with Shift).
- Select other: ` / ~ key cycles among all entities hit by the last ray (closest first).
- Mode keys: O (object), E (edge), T (face).
- Pure helpers `hit_test_edges_along_ray` and `hit_test_faces_along_ray` return sorted (index, distance) lists for multi and cycling.
- Tests added for the multi-hit helpers.

## Implementation status (2026-11-27)
- Multi-hit helpers `hit_test_edges_along_ray` and `hit_test_faces_along_ray` implemented and tested.
- ViewportWidget supports:
  - selection_mode object/edge/face (keys O/E/T)
  - Shift+click additive multi-select
  - Box select (drag in edge/face mode)
  - Select other (~ / ` cycles last ray hits)
  - Green highlight for selected edges or face boundaries
  - entity_selection_changed signal
- get_entity_selection_string returns comma-separated indices for property panel use.
