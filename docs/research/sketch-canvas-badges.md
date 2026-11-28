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

Next polish ideas: group move-together for ordinate sets, origin indicator, optional QtSvg for more complex icons.
