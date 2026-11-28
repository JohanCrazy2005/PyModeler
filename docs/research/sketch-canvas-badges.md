# Sketch Canvas Constraint & Dimension Badges

Research notes for canvas badge polish (glyphs, hover, visibility toggle, double-click edit, related selection, drag, in-place edit, vector glyphs).

## How other tools do it

- **Fusion 360**: Sketch constraints appear as small glyph icons (H, V, parallel lines, etc.) near the constrained geometry. Hovering highlights the icon and shows a tooltip. Dimensions are fully interactive: double-click or click the value to edit in place. Visibility can be toggled via the sketch palette or display settings. Clicking a constraint icon selects the related geometry. Users can drag dimension text for placement.
- **Onshape**: Similar constraint icons with hover feedback. Hover over a constraint icon highlights the related entities in yellow. Dimension values are editable by double-click. Users can hide/show constraints and dimensions independently. Constraint icons can be dragged to reposition for better visibility (Constraint Manager tip). Icons are vector-style symbols (parallel bars, perpendicular L, equal bars, concentric circles, etc.).
- **Mozaik / shop tools**: Focus more on manufacturing dimensions; constraint glyphs are less common but dimension edit-by-click is standard.

## This increment (2026-11-27)

- Improved glyph labels (H/V/C/= /⊥ // etc.) with better visual styling (colored text + implicit background via z-order).
- `show_badges` flag + `set_show_badges()` for visibility toggle.
- Hover highlight (brighter text color) on badge under cursor + related entities highlighted (cyan).
- Click on badge selects the related entities.
- Double-click on dimension badge opens in-place text edit (QGraphicsTextItem interaction) instead of modal dialog; commits on focus loss / Enter.
- Badges support drag-to-reposition: offset stored in `parameters["badge_offset"]` on the constraint or dimension (schema-compatible via parameters additionalProperties).
- Badges store type + index + related entity IDs in item data (2/3/4).
- Full SketchCanvasWidget remains intact.
- **True vector SVG-style glyphs**: Constraint badges now render as `QGraphicsPathItem` using `QPainterPath` definitions (horizontal/vertical lines, parallel bars, perpendicular L, equal bars, concentric circles, midpoint triangle, coincident dots, tangent, fixed). Scales cleanly, looks like CAD icons. Dimensions remain editable text. Hover brightens path pen/brush.

Next polish ideas: dimension leader line visualization on canvas, optional QtSvg for more complex icons.

## Ordinate Badge Alignment Snapping (2026-11-27)

**Research**: Fusion 360 and Onshape ordinate dimensions keep leaders axis-aligned (horizontal for X-ordinates, vertical for Y). Groups stack with consistent spacing; dragging one snaps others into alignment. Users expect leaders to "stick" to the axis when close.

**Implementation**:
- `_snap_ordinate_badge` in SketchCanvasWidget.
- For axis="x" snaps badge Y to origin Y (or nearby group mate Y) within 6 units.
- For axis="y" snaps badge X to origin X (or group mate X).
- Applied live during drag and used for the committed `badge_offset` on release.
- Tests cover origin snap and group-mate snap.

This completes the "badge alignment snapping for ordinate leaders" item from NEXT_STEPS.

## Dimension Leader Line Visualization (2026-11-27)

**Research**: Fusion 360 and Onshape display dimension text with leader lines (or extension lines) that connect the value to the measured geometry. Leaders are typically axis-aligned for linear/ordinate dimensions and radial for radius/diameter. The text can be dragged and the leaders update.

**Implementation**:
- `_draw_dimension_leaders` in SketchCanvasWidget draws thin dashed leader lines after badges.
- For ordinary dimensions a straight leader goes from the badge position to the entity attachment point (midpoint/center).
- For ordinate dimensions the leader is axis-aligned: horizontal-then-vertical (or vice-versa) so it matches the snapped badge alignment.
- Leader items are tagged with `data(1)="leader"` and `data(2)="dimension_leader"` for test inspection.
- Cosmetic pen so lines stay thin under zoom.
- Covered by `test_dimension_leader_lines_drawn`.

This completes the "dimension leader line visualization on canvas" item from NEXT_STEPS.

## Dimension Leaders with Arrowheads and Extension Lines (2026-11-28)

**Research**: Fusion 360 and Onshape show linear dimensions with extension lines that project past the measured geometry and arrowheads (or tick marks) at the dimension line ends. Leaders for dragged text are usually thin, dashed or solid, and update live. Ordinate dimensions keep axis-aligned leaders ending in a small tick or arrow at the measured point.

**Implementation**:
- `_draw_dimension_leaders` draws dashed cosmetic leaders from the dimension badge position to the geometry attachment point.
- Linear / aligned / distance dimensions receive a short extension segment past the attach point.
- Ordinate dimensions use axis-aligned two-segment leaders matching the existing badge snap behavior.
- `_add_arrowhead` draws a small open V-shaped arrowhead at the attachment point.
- Leader and arrow items tagged with `data(1)="leader"` (and `data(2)` for type) so tests can inspect them.
- Covered by `test_dimension_leader_lines_and_arrowheads`.

This completes the further canvas polish item (extension lines + arrowheads on leaders) from NEXT_STEPS.
