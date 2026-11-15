# Development Checklist

Status legend: [ ] Todo  [~] In progress  [x] Done  [-] Deferred

## Phase 0 – Foundation
- [x] Create public GitHub repository
- [x] Define GOAL, PLAN, CHECKLIST, NEXT_STEPS
- [x] Project skeleton with src/, schemas/, tests/, docs/, output/
- [x] JSON Schema for core Mesh data model (legacy / utility)
- [x] JSON Schema for Scene
- [x] Basic PyQt6 application window
- [x] Cross-platform dependency list
- [x] Automated tests for core data + smoke test
- [ ] Continuous integration skeleton (GitHub Actions)
- [ ] Ensure all core source modules are complete and tested on main

## Research & Planning (Mandatory)
- [ ] Create `docs/research/` folder
- [ ] Research notes: Fusion 360 parametric modeling, sketches, features, assemblies, CAM overview
- [ ] Research notes: Onshape Part Studios, feature history, configurations, collaboration model
- [ ] Research notes: Mozaik cut lists, nesting, joinery, hardware, G-code / manufacturing outputs
- [ ] Prioritized feature inventory document aligned with Fusion/Onshape/Mozaik goal
- [ ] Refine PLAN.md and this CHECKLIST with concrete next implementation steps

## Phase 1 – Parametric Core (Sketch + Features)
- [ ] Sketch schema + data model (entities, constraints, dimensions)
- [ ] Basic 2D sketch editor in UI
- [ ] Extrude feature (from sketch to solid) with parameters
- [ ] Feature history / timeline data model + simple UI
- [ ] Revolve feature
- [ ] Basic parameters / variables system

## Phase 2 – Parts, Assemblies & Manufacturing Helpers
- [ ] Multi-feature Part model
- [ ] Simple Assembly + mates / constraints
- [ ] Cut list / part list generation (Mozaik-inspired)
- [ ] Basic BOM
- [ ] Dimensioned drawing / export stubs
- [ ] Material / stock definitions

## Phase 3 – Viewport, Interaction & Polish
- [ ] Real OpenGL / moderngl viewport
- [ ] Camera controls, selection, feature highlighting
- [ ] Transform tools that respect parametric intent where possible

## Phase 4 – Advanced CAD + Path to CAM
- [ ] Fillet / Chamfer / Shell / Hole features
- [ ] Configurations
- [ ] Sheet metal / panel basics
- [ ] Simple nesting concepts
- [ ] Early toolpath / G-code generation stubs
- [ ] Import/Export improvements (STEP later if geometry kernel allows)

## Ongoing
- [ ] Keep all data structures under JSON Schemas
- [ ] Tests for every new module before push
- [ ] Update PLAN.md and NEXT_STEPS.md after every significant run
- [ ] Maintain research docs as the product evolves

Last updated: 2026-11-14 (goal pivoted to Fusion 360 / Onshape / Mozaik style)
