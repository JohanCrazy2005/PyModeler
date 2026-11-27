# Sketch Canvas Constraint & Dimension Badges

Research notes for canvas badge polish (glyphs, hover, visibility toggle, double-click edit).

## How other tools do it

- **Fusion 360**: Sketch constraints appear as small glyph icons (H, V, parallel lines, etc.) near the constrained geometry. Hovering highlights the icon and shows a tooltip. Dimensions are fully interactive: double-click or click the value to edit in place. Visibility can be toggled via the sketch palette or display settings.
- **Onshape**: Similar constraint icons with hover feedback. Dimension values are editable by double-click. Users can hide/show constraints and dimensions independently.
- **Mozaik / shop tools**: Focus more on manufacturing dimensions; constraint glyphs are less common but dimension edit-by-click is standard.

## This increment

- Short glyph labels (H/V/C/= /⊥ etc.) already present.
- Added `show_badges` flag + `set_show_badges()` for visibility toggle.
- Hover highlight (brighter text color) on badge under cursor.
- Double-click on dimension badge opens QInputDialog to edit the value and refresh.
- Badges store type + index in item data for reliable identification.

Next polish ideas: proper SVG glyphs, group selection of related constraints, in-place text edit instead of dialog.
