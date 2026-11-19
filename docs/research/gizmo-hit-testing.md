# Gizmo Hit-Testing Polish

## Research notes

Fusion 360 and Onshape transform gizmos use:
- Thick arrow shafts + large arrowheads for translation (hit priority on the head)
- Circular rings (or arcs) for rotation, tested by ray-plane intersection + radius band
- End cubes / handles for scale
- Visual feedback: the active handle brightens or changes color while dragging

Onshape's Transform dialog and Fusion's Move/Copy both keep free transforms out of the parametric history when possible, preferring sketch or parameter updates.

## This increment

- Pure `hit_test_gizmo_axis` prefers tips (translate), rings (rotate), markers (scale).
- Viewport uses it; active axis is drawn brighter yellow while dragging.
- MainWindow restored (was empty on main) and wires `transform_committed` to parametric translation.
- Headless-safe pure helpers + tests.
