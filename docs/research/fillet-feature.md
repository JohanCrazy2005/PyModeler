# Fillet Feature

Research notes for the Fillet (edge rounding) feature in Fusion 360, Onshape, and manufacturing-oriented tools.

## Fusion 360

- Dedicated **Fillet** tool under Design > Solid > Modify > Fillet.
- Selection: edges, faces (all edges of face), or features.
- Radius types: Constant, Chord Length, Variable (points along edge), Asymmetric.
- Continuity: Tangent (G1) or Curvature (G2).
- Corner types: Rolling Ball, Setback.
- Supports multiple selection sets with independent radii.
- Parametric; radius can be driven by parameters.
- Rolling-ball method: ball of given radius rolled along the edge, tangent to adjacent faces.

Sources: Autodesk Fusion Help – Fillet reference, Create a fillet.

## Onshape

- Fillet feature (shortcut Shift+F) for edge fillets and full-round fillets.
- Edge or face selection; tangent propagation option.
- Measurement: Radius or Width.
- Control: Distance (circular), Conic (with Rho), Curvature.
- Variable radius, asymmetric, partial fillet options.
- Best practice: structural fillets before finish fillets; larger radii before smaller; shell after fillets.

Sources: Onshape Help – Fillet; Tech Tips on fillet types.

## Manufacturing relevance

- Fillets reduce stress concentrations, improve machinability (tool access), and are common in cast, molded, and CNC parts.
- Dedicated feature enables parametric control, drawing callouts, and future CAM toolpath awareness (avoid sharp internal corners).

## Implications for PyModeler

Current mesh-based approach:

1. Schema for FilletFeature with radius (numeric or parameter), optional edge selection (list of edge indices or identifiers), operation="modify".
2. Stub implementation: store the intent; generate a placeholder mesh or note that full rolling-ball / edge fillet on mesh is deferred (requires robust B-rep or advanced mesh bevel).
3. Integrate into FeatureHistory so it appears in the timeline and can be suppressed/rollback.
4. Later: basic mesh bevel approximation for selected edges, or wait for geometry kernel.

This continues Phase 4 advanced features after Hole.
