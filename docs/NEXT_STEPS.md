# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority
1. **Research & Documentation (do this now)**
   - Create `docs/research/` folder.
   - Write structured notes on:
     - Fusion 360 parametric modeling + sketch + feature workflow
     - Onshape Part Studio / feature history / configurations approach
     - Mozaik cut-list, nesting, joinery, and manufacturing output features
   - Produce a prioritized feature inventory aligned with the new CAD/CAM goal.
2. Update CHECKLIST and PLAN with more concrete items derived from the research.
3. Finish any missing foundation modules so the current app runs cleanly and all tests pass.
4. Then begin the parametric core according to the refined plan:
   - Sketch data model + schema
   - Basic constrained sketch
   - Extrude feature that produces a solid from a sketch
   - Feature history / timeline UI stub

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- Keep JSON schemas as the source of truth for all data.
- Test before every push. Keep main runnable.
- Put research outputs in `docs/research/` and any generated examples in `output/`.
