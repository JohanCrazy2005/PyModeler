# Configurations (Independent Inputs)

Research notes for PyModeler. Sources: Onshape Help / Learning Center, Autodesk Fusion configurations documentation. Last updated: 2026-11-18.

## Onshape Approach (preferred reference)
- Configurations use **independent inputs** instead of one giant combinatorial table.
- Input types:
  - **List** – discrete options (e.g., Small / Medium / Large). Each option can drive multiple parameters or suppress features.
  - **Checkbox / Boolean** – on/off (commonly used to suppress a feature or set a 0/1 value).
  - **Configuration Variable** – numeric (or text) value that can be set when inserting the configured part.
- Each input is managed in its own small table / control.
- Configured Part Studios can be inserted into assemblies; the user supplies values for the inputs.
- Avoids exponential growth of design tables.

## Fusion 360 Approach
- Configuration Table (rows = configurations, columns = configurable aspects).
- Configurable aspects include user parameters, feature parameters, suppressions, materials, appearances, etc.
- Theme tables for grouping related aspects.
- More spreadsheet-like; still powerful but can become large.

## Implementation Decision for PyModeler
Follow the Onshape-style independent-input model for simplicity and scalability:
- `ConfigurationSet` holds a list of independent inputs (list / numeric / boolean).
- Applying a selection updates `ParameterStore` values and marks features `suppressed`.
- FeatureHistory.recompute_meshes already respects the `suppressed` flag.
- Stored optionally on a Part so the configuration definition travels with the part.
- Schema-driven so designs remain transparent.

## Next Possible Enhancements
- UI panel to select current configuration values.
- Assembly instances that store chosen configuration selections.
- More sophisticated option logic (expressions, conditional suppressions).
- Configuration rules / constraints between inputs.

## References
- Onshape Help: Configurations
- Onshape Learning Center: Configurations pathway
- Autodesk Fusion: Configurations overview
