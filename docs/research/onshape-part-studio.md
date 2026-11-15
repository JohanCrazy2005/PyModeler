# Onshape Part Studio, Feature History, and Configurations

Research notes for PyModeler. Sources: Onshape official help (cad.onshape.com), Learning Center, and product documentation. Last updated: 2026-11-15.

## Part Studio Concept
- A **Part Studio** is a design environment (not a single part file) for creating parts, surfaces, and sketches that share common references.
- Contains: Feature toolbar, Feature list (parametric history), graphics area.
- Multiple distinct parts can live in one Part Studio and share sketches/references (multi-part Part Studio).
- Use when parts should update together (shared mounting sketch, family of parts, etc.).
- Assemblies are separate: they define relationships/motion between parts from one or more Part Studios.
- Derived parts / in-context features allow controlled sharing across studios while keeping studios smaller.

## Feature History
- Every Part Studio has a Feature list (timeline) that drives the geometry.
- Features include sketches, extrudes, revolves, fillets, patterns, custom FeatureScript features, etc.
- Editing a feature earlier in the list recomputes subsequent features.
- Features can be suppressed.
- The Feature list is the single source of truth for the shape of the parts in that studio.

## Configurations
Onshape's configuration system is modern and flexible (avoids huge design tables):
- One Configuration panel per Part Studio / Assembly / Variable Studio.
- Multiple independent **configuration inputs** (not one giant table):
  - List inputs (discrete options)
  - Checkbox inputs (on/off, e.g., suppress a feature)
  - Configuration variables (numeric or text values)
- Can configure almost anything: feature depths, suppressions, FeatureScript parameters, part numbers, colors, materials, sketch text, etc.
- Independent inputs keep management simple even for complex families.
- Configured Part Studios can be inserted into assemblies; the user picks values for each input.
- Useful for part families, variants, and manufacturing options.

## Key Takeaways for PyModeler
- Feature history / timeline data model is central (similar to Fusion).
- Support multi-feature parts (and later multi-part documents) cleanly.
- Configurations are a high-value later feature: independent parameters that drive feature inputs and suppressions.
- Keep data JSON-schema driven so designs remain transparent and versionable (Onshape's cloud architecture highlights the value of clean data).
- Clear separation between modeling environment (Part) and assembly environment.

## References
- Onshape Help: Part Studios, Configurations
- Onshape Learning Center: Configurations pathway
- Multi-part Part Studio vs Assembly distinctions
