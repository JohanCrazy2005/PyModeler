# Shell Feature

Research notes for the Shell (hollow / thin-wall) feature in Fusion 360, Onshape, and manufacturing-oriented tools.

## Fusion 360

- Dedicated **Shell** tool under Design > Solid > Modify > Shell.
- Select one or more faces to remove (these become openings). The remaining body is hollowed to a constant wall thickness.
- Alternatively, select the entire body (no faces) to create a fully enclosed hollow cavity.
- Thickness direction options: Inside (outer dimensions unchanged), Outside (part grows), Both.
- Thickness can be driven by parameters.
- Rounded Shell option available for outside shells (adds fillets to outer edges).
- Best practice: apply structural fillets before shelling so internal corners are handled; shell thickness must be smaller than local feature radii or opposing walls will collide.
- Common failures: self-intersections when thickness exceeds local curvature or when walls are closer than 2× thickness.

Sources: Autodesk Fusion Help – Shell, various tutorial analyses (inside/outside/both, face selection order).

## Onshape

- Shell feature in Part Studio toolbar.
- Select faces to remove; rest of the part is hollowed to constant wall thickness.
- Optional “Hollow” checkbox to shell without removing any faces (fully enclosed cavity).
- Direction: default inside; toggle opposite direction for outside.
- Thickness is a numeric value or variable.
- Feature order matters: features after the shell are not affected by the shell; features before can be excluded by reordering.
- Failures occur with high curvature relative to thickness or thin opposing walls. Workarounds include shelling in stages or manual offset + Boolean subtract.

Sources: Onshape Help – Shell; troubleshooting tech tips.

## Manufacturing relevance

- Essential for injection-molded plastic parts, castings, and 3D-printed thin-wall designs.
- Uniform wall thickness improves material flow, cooling, and strength-to-weight.
- Parametric thickness enables design variations and matches manufacturing constraints (minimum wall, draft later).
- Opens the path toward sheet-metal / panel thinking and nesting-friendly part definitions.

## Implications for PyModeler

Current mesh-based approach:

1. Schema for ShellFeature with thickness (numeric or parameter), optional faces list (identifiers or indices to remove), direction (inside/outside/both), operation="modify".
2. Basic mesh shell approximation in apply_to_mesh: offset vertices along averaged face normals by thickness * miter_scale (where miter_scale averages 1/(vn·nf) to better approximate constant thickness at sharp corners), create outer + inner surfaces (reversed winding), and connecting wall faces. Integer face indices are treated as openings (omitted from outer/inner).
3. Integrate into FeatureHistory and Part.recompute (modify path).
4. Placeholder generate_mesh for timeline visibility when no body exists.
5. Later: true Boolean offset (scale-from-centroid + cut), further corner improvements, manifold cleanup, or a robust geometry kernel.

This continues Phase 4 advanced features after Hole / Fillet / Chamfer.

## Update 2026-11-24 – Openings with rim walls + named faces

- Opening faces (removed faces) now produce **explicit rim walls** on their boundary edges so the shell thickness is visible at the lip (matches Fusion/Onshape behavior of a clean open shell).
- Face selection accepts integer indices, digit-strings, and named labels: `top`, `bottom`, `front`, `back`, `left`, `right` (resolved from dominant face-normal axis).
- Wall-edge collection includes both kept-face edges and opening-boundary edges; outer/inner surfaces still omit the open faces.
- Tests: `test_shell_opening_has_rim_walls`, `test_shell_named_face_opening`, `test_shell_string_index_face`.
