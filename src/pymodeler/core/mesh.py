"""Mesh data model with JSON Schema validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional, Sequence

import jsonschema
from jsonschema import Draft202012Validator

# Resolve schema path relative to this file
_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_MESH_SCHEMA_PATH = _SCHEMA_DIR / "mesh.schema.json"

with open(_MESH_SCHEMA_PATH, encoding="utf-8") as f:
    MESH_SCHEMA = json.load(f)

_MESH_VALIDATOR = Draft202012Validator(MESH_SCHEMA)


class MeshValidationError(ValueError):
    """Raised when mesh data fails schema validation."""


def validate_mesh_data(data: dict) -> None:
    """Validate a dict against the Mesh JSON Schema. Raises MeshValidationError on failure."""
    errors = sorted(_MESH_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise MeshValidationError("Mesh schema validation failed:\n" + "\n".join(messages))


class Mesh:
    """In-memory mesh that stays schema-compliant."""

    def __init__(
        self,
        vertices: Sequence[Sequence[float]],
        faces: Sequence[Sequence[int]],
        name: str = "Mesh",
        edges: Optional[Sequence[Sequence[int]]] = None,
        normals: Optional[Sequence[Sequence[float]]] = None,
        uvs: Optional[Sequence[Sequence[float]]] = None,
        metadata: Optional[dict] = None,
    ):
        self.name = name
        self.vertices: List[List[float]] = [list(map(float, v)) for v in vertices]
        self.faces: List[List[int]] = [list(map(int, f)) for f in faces]
        self.edges = [list(map(int, e)) for e in edges] if edges is not None else None
        self.normals = [list(map(float, n)) for n in normals] if normals is not None else None
        self.uvs = [list(map(float, u)) for u in uvs] if uvs is not None else None
        self.metadata = metadata or {}

        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "name": self.name,
            "vertices": self.vertices,
            "faces": self.faces,
        }
        if self.edges is not None:
            data["edges"] = self.edges
        if self.normals is not None:
            data["normals"] = self.normals
        if self.uvs is not None:
            data["uvs"] = self.uvs
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_mesh_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Mesh":
        validate_mesh_data(data)
        return cls(
            vertices=data["vertices"],
            faces=data["faces"],
            name=data.get("name", "Mesh"),
            edges=data.get("edges"),
            normals=data.get("normals"),
            uvs=data.get("uvs"),
            metadata=data.get("metadata"),
        )

    def __repr__(self) -> str:
        return f"<Mesh name={self.name!r} verts={len(self.vertices)} faces={len(self.faces)}>"


def create_cube(size: float = 2.0, name: str = "Cube") -> Mesh:
    """Create a unit cube centered at origin, scaled by size/2."""
    s = size / 2.0
    vertices = [
        [-s, -s, -s],
        [s, -s, -s],
        [s, s, -s],
        [-s, s, -s],
        [-s, -s, s],
        [s, -s, s],
        [s, s, s],
        [-s, s, s],
    ]
    # 6 faces, each a quad (order matters for winding)
    faces = [
        [0, 1, 2, 3],  # bottom
        [4, 5, 6, 7],  # top
        [0, 1, 5, 4],  # front
        [2, 3, 7, 6],  # back
        [0, 3, 7, 4],  # left
        [1, 2, 6, 5],  # right
    ]
    return Mesh(vertices=vertices, faces=faces, name=name)
