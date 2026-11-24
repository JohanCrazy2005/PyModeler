# Toolpath Spiral Strategy Research

## Fusion 360 / Autodesk Fusion
- Pocket strategies include Adaptive, Contour, and Spiral (especially useful for circular or smooth pockets).
- Spiral reduces tool engagement variation and can improve surface finish / tool life vs pure concentric rectangles.
- Supports lead-in/out, corner radius (fillets on path), and stepover.

## Onshape
- CAM Studio (or connected apps) offers spiral and morphing strategies for pockets.
- Emphasizes continuous paths to minimize retracts.

## Mozaik / Manufacturing tools
- More focused on nesting and 2.5D panels; spiral less common but rectangular pocket clearing with rounded corners is standard for CNC routers.

## Implementation notes for PyModeler
- Current rectangular spiral (connected inset rectangles) already provides continuous tool-down path per Z-level.
- Adding corner-radius arcs (G03) reuses the existing `corner_radius` parameter already used by concentric/contour.
- True Archimedean (polar) spiral is better for circular pockets; for rectangular features the morphing/rectangular spiral with arcs is a practical, manufacturable approximation that avoids sharp 90° corners.
- Future: polar spiral mode when width ≈ height, or full morphing algorithm.

## Archimedean (polar) spiral addition (2026-11-23)
- True Archimedean spiral r = a - b·θ on the inscribed circle of the rectangular pocket.
- Approximated by short linear G01 segments (practical for most controllers; true G2/G3 with varying radius is controller-specific).
- Radial pitch controlled by existing stepover_fraction.
- One continuous tool-down path per Z-level after the initial plunge.
- Best for square or near-circular pockets; rectangular pockets use the inscribed diameter so corners of the rectangle are left for a later contour or larger stepover.
- References: same as above + Siemens/LinuxCNC Archimedean spiral examples.

References:
- Romero-Carrillo et al., Analytic construction of spiral pocketing via linear morphing (CAD 2015).
- Siemens Sinumerik documentation on Archimedean spiral via modified tool radius compensation.
