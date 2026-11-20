"""Parametric Part: aggregates sketches, parameters, and FeatureHistory into a recomputable body.

Validated against schemas/part.schema.json.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema
from jsonschema import Draft202012Validator

from .boolean import mesh_boolean
from .features import FeatureHistory, FeatureValidationError
from .mesh import Mesh
from .parameters import ParameterStore
from .sketch import Sketch
from .configurations import ConfigurationSet

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_PART_SCHEMA_PATH = _SCHEMA_DIR / "part.schema.json"

with open(_PART_SCHEMA_PATH, encoding="utf-8") as f:
    PART_SCHEMA = json.load(f)

_PART_VALIDATOR = Draft202012Validator(PART_SCHEMA)


class PartValidationError(ValueError):
    """Raised when Part data fails schema validation."""


def validate_part_data(data: dict) -> None:
    errors = sorted(_PART_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise PartValidationError("Part schema validation failed:\n" + "\n".join(messages))


def _new_id(prefix: str = "part") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class Part:
    """A single parametric part built from sketches + feature history."""

    def __init__(
        self,
        name: str = "Part",
        sketches: Optional[Dict[str, Sketch]] = None,
        parameters: Optional[ParameterStore] = None,
        feature_history: Optional[FeatureHistory] = None,
        configurations: Optional[ConfigurationSet] = None,
        material: Optional[Any] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id()
        self.name = name
        self.sketches: Dict[str, Sketch] = sketches or {}
        self.parameters = parameters or ParameterStore(name=f"{name} Parameters")
        self.feature_history = feature_history or FeatureHistory(name=f"{name} History")
        self.configurations = configurations
        self.material = material
        self.metadata = metadata or {}
        self._body: Optional[Mesh] = None
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "sketches": {sid: sk.to_dict() for sid, sk in self.sketches.items()},
            "parameters": self.parameters.to_dict(),
            "feature_history": self.feature_history.to_dict(),
        }
        if self.configurations is not None:
            data["configurations"] = self.configurations.to_dict()
        if self.material is not None:
            data["material"] = self.material
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_part_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Part":
        validate_part_data(data)
        sketches = {}
        for sid, sdata in data.get("sketches", {}).items():
            sketches[sid] = Sketch.from_dict(sdata)
        parameters = ParameterStore.from_dict(data.get("parameters", {}))
        history = FeatureHistory.from_dict(data.get("feature_history", {}))
        configurations = None
        if "configurations" in data and data["configurations"]:
            configurations = ConfigurationSet.from_dict(data["configurations"])
        return cls(
            name=data.get("name", "Part"),
            sketches=sketches,
            parameters=parameters,
            feature_history=history,
            configurations=configurations,
            material=data.get("material"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def add_sketch(self, sketch: Sketch) -> None:
        self.sketches[sketch.id] = sketch
        self.validate()

    def recompute(self) -> Optional[Mesh]:
        """Recompute the part body from active features.

        Applies operations according to each feature's `operation` field:
        - "new" or first solid feature: starts the body
        - "join": mesh_boolean join
        - "cut": mesh_boolean cut (difference)
        - "modify": in-place mesh modification (Fillet / Chamfer bevel)
        Falls back gracefully when the Boolean engine is unavailable.
        Returns the resulting Mesh or None if no features produced geometry.
        """
        from .features import FilletFeature, ChamferFeature

        active = self.feature_history.active_features()
        if not active:
            self._body = None
            return None

        # Pre-generate tool meshes for features that produce independent geometry
        meshes = self.feature_history.recompute_meshes(self.sketches, self.parameters)

        body: Optional[Mesh] = None
        for fdict in active:
            fid = fdict.get("id", "feat")
            ftype = fdict.get("type")
            op = fdict.get("operation", "join")

            # Modify features act on the current body
            if ftype in ("fillet", "chamfer") and op == "modify":
                if body is None:
                    continue
                try:
                    if ftype == "fillet":
                        feat = FilletFeature.from_dict(fdict)
                        body = feat.apply_to_mesh(body, self.parameters)
                    else:
                        feat = ChamferFeature.from_dict(fdict)
                        body = feat.apply_to_mesh(body, self.parameters)
                    body.name = f"{self.name}_{fid}"
                except Exception:
                    # Keep previous body if bevel fails
                    pass
                continue

            mesh = meshes.get(fid)
            if mesh is None:
                continue
            mesh.name = f"{self.name}_{fid}"

            if body is None or op == "new":
                body = mesh
            else:
                bool_op = "cut" if op == "cut" else "join"
                try:
                    body = mesh_boolean(body, mesh, bool_op, name=self.name)
                except Exception:
                    if bool_op == "join":
                        body = mesh_boolean(body, mesh, "join", name=self.name)
                    # else: leave body unchanged on cut failure

        self._body = body
        return body

    @property
    def body(self) -> Optional[Mesh]:
        if self._body is None:
            self.recompute()
        return self._body

    def __repr__(self) -> str:
        return f"<Part id={self.id!r} name={self.name!r} features={len(self.feature_history.features)}>"
