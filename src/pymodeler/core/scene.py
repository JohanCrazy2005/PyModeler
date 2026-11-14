"""Scene graph: objects with transforms. Validated against JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

import jsonschema
from jsonschema import Draft202012Validator

from .mesh import Mesh, validate_mesh_data

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_SCENE_SCHEMA_PATH = _SCHEMA_DIR / "scene.schema.json"

with open(_SCENE_SCHEMA_PATH, encoding="utf-8") as f:
    SCENE_SCHEMA = json.load(f)

_SCENE_VALIDATOR = Draft202012Validator(SCENE_SCHEMA)


class SceneValidationError(ValueError):
    """Raised when scene data fails schema validation."""


def validate_scene_data(data: dict) -> None:
    """Validate a dict against the Scene JSON Schema."""
    errors = sorted(_SCENE_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise SceneValidationError("Scene schema validation failed:\n" + "\n".join(messages))


class Transform:
    """Location, rotation (Euler XYZ radians), scale."""

    def __init__(
        self,
        location: Optional[list[float]] = None,
        rotation: Optional[list[float]] = None,
        scale: Optional[list[float]] = None,
    ):
        self.location = list(location) if location is not None else [0.0, 0.0, 0.0]
        self.rotation = list(rotation) if rotation is not None else [0.0, 0.0, 0.0]
        self.scale = list(scale) if scale is not None else [1.0, 1.0, 1.0]

    def to_dict(self) -> dict:
        return {
            "location": self.location,
            "rotation": self.rotation,
            "scale": self.scale,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "Transform":
        if not data:
            return cls()
        return cls(
            location=data.get("location"),
            rotation=data.get("rotation"),
            scale=data.get("scale"),
        )


class SceneObject:
    """An object in the scene that holds a Mesh and a Transform."""

    def __init__(
        self,
        name: str,
        mesh: Mesh,
        transform: Optional[Transform] = None,
        visible: bool = True,
        metadata: Optional[dict] = None,
    ):
        self.name = name
        self.mesh = mesh
        self.transform = transform or Transform()
        self.visible = visible
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "name": self.name,
            "mesh": self.mesh.to_dict(),
            "visible": self.visible,
        }
        t = self.transform.to_dict()
        if t != {"location": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]}:
            data["transform"] = t
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "SceneObject":
        mesh = Mesh.from_dict(data["mesh"])
        transform = Transform.from_dict(data.get("transform"))
        return cls(
            name=data["name"],
            mesh=mesh,
            transform=transform,
            visible=data.get("visible", True),
            metadata=data.get("metadata"),
        )


class Scene:
    """Collection of SceneObjects with basic object-mode selection."""

    def __init__(self, name: str = "Scene", objects: Optional[List[SceneObject]] = None):
        self.name = name
        self.objects: List[SceneObject] = objects or []
        self._selected_names: set[str] = set()

    def add_object(self, obj: SceneObject) -> None:
        self.objects.append(obj)

    def get_object(self, name: str) -> Optional[SceneObject]:
        for obj in self.objects:
            if obj.name == name:
                return obj
        return None

    # ------------------------------------------------------------------
    # Selection (object mode)
    # ------------------------------------------------------------------

    def select(self, obj_or_name: SceneObject | str, clear: bool = True) -> None:
        """Select an object. If clear=True, deselect others first."""
        name = obj_or_name.name if isinstance(obj_or_name, SceneObject) else obj_or_name
        if self.get_object(name) is None:
            return
        if clear:
            self._selected_names.clear()
        self._selected_names.add(name)

    def deselect(self, obj_or_name: SceneObject | str) -> None:
        name = obj_or_name.name if isinstance(obj_or_name, SceneObject) else obj_or_name
        self._selected_names.discard(name)

    def clear_selection(self) -> None:
        self._selected_names.clear()

    def is_selected(self, obj_or_name: SceneObject | str) -> bool:
        name = obj_or_name.name if isinstance(obj_or_name, SceneObject) else obj_or_name
        return name in self._selected_names

    def selected_objects(self) -> List[SceneObject]:
        """Return currently selected SceneObjects (in scene order)."""
        return [obj for obj in self.objects if obj.name in self._selected_names]

    def selected_names(self) -> set[str]:
        return set(self._selected_names)

    # ------------------------------------------------------------------
    # Serialization (selection is not persisted)
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "name": self.name,
            "objects": [o.to_dict() for o in self.objects],
        }
        return data

    def validate(self) -> None:
        validate_scene_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        validate_scene_data(data)
        objects = [SceneObject.from_dict(o) for o in data["objects"]]
        return cls(name=data.get("name", "Scene"), objects=objects)

    def __repr__(self) -> str:
        return f"<Scene name={self.name!r} objects={len(self.objects)} selected={len(self._selected_names)}>"
