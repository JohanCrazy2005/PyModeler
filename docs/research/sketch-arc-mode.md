# Sketch Arc Creation Research

## Fusion 360
- **Center Point Arc**: Click center, then start point (defines radius + start angle), then end point (or angle value). Live preview of the arc.
- **3-Point Arc**: Click two endpoints, then a third point on the arc to define radius/bulge.
- **Tangent Arc**: Two points that maintain tangency to existing geometry.
- Snapping and automatic constraints are common.

## Onshape
- **Center Point Arc**: Center → start (radius) → end.
- **3-Point Arc**: Start → end → through-point.
- Multiple variants (elliptical, conic) available later.

## Implementation choice (this run)
Implemented **Center Point Arc** style matching Fusion/Onshape:
1. Click center
2. Click start point (sets radius + start_angle)
3. Click end point (sets end_angle, positive CCW sweep)
Live preview: full circle during step 2, arc during step 3.

Future: optional 3-point arc mode.
