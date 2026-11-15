# Feature Tree / Timeline UI Research

**Sources**: Fusion 360 Help (Use the Timeline), Onshape Feature List documentation and tech tips, community overviews.

**Date**: 2026-11-15

## Core Concept

Parametric CAD systems maintain a history of features (sketches, extrudes, revolves, etc.) that can be viewed, selected, edited, and reordered. The UI for this is typically:

- **Fusion 360**: Bottom horizontal Timeline strip of feature icons + left Browser tree (components, bodies, sketches). Selection highlights both. Double-click or right-click to edit. Rollback marker.
- **Onshape**: Left-side Feature List (vertical) showing ordered features with icons, names, and a rollback bar. Parts list below. Search/filter, folders for organization. Property/dialog panels open on edit.

## Practical Implementation for PyModeler (Phase 1 stub)

1. Vertical QTreeWidget or QListWidget on the left or right of the main window showing FeatureHistory items (name + type).
2. Selecting a feature populates a simple Property panel (QFormLayout) showing editable fields such as distance (numeric or parameter name string).
3. Changes to properties update the underlying FeatureHistory and can trigger recompute later.
4. No full edit dialogs or rollback yet — just display, select, and basic property inspection/editing.
5. Integrates with existing MainWindow without breaking current mesh/outliner workflow.

This guides the first Timeline/Feature Tree UI stub.
