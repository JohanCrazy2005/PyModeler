# PyModeler

Cross-platform 3D modeling software built with **PyQt6**, pure Python, and strict **JSON Schemas**.

## Vision
Incrementally build a modeling application that eventually provides the core capabilities of top tools such as Blender, Maya, and 3ds Max. Development is structured, documented, and driven by living planning documents under `docs/`.

## Current Status (v0.1.0)
- Public repository + project skeleton
- JSON Schemas for Mesh and Scene
- Validated Mesh class + primitives (Cube, Plane, Sphere, Cylinder, Cone)
- Scene / SceneObject with transforms
- PyQt6 main window with outliner, properties, and **OpenGL viewport**
- Viewport: ground grid, RGB axes, wireframe meshes, orbit / pan / zoom camera
- "Add → Mesh → ..." works, validates against schema, and updates the viewport
- Automated tests for schema + mesh creation + app launch
- GitHub Actions CI (pytest with QT_QPA_PLATFORM=offscreen)

See `docs/GOAL.md`, `docs/CHECKLIST.md`, `docs/PLAN.md`, and `docs/NEXT_STEPS.md` for the full roadmap.

## Quick Start

```bash
# Clone
git clone https://github.com/JohanCrazy2005/PyModeler.git
cd PyModeler

# Create virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install
pip install -e ".[dev]"

# Run
python -m pymodeler.ui.main_window
# or
pymodeler
```

## Project Layout
```
PyModeler/
├── docs/           # GOAL, CHECKLIST, PLAN, NEXT_STEPS
├── schemas/        # JSON Schemas (source of truth)
├── src/pymodeler/  # Application code
│   ├── core/       # Mesh, Scene (no Qt)
│   └── ui/         # PyQt6 windows & widgets
├── tests/
├── output/         # Build / export artifacts (as requested)
└── requirements.txt
```

## Automation
An hourly automation is planned to read the living documents, implement the next highest-value item, test it, update the docs, and push. The main branch should always remain runnable.

## License
MIT
