"""Additional features: Fillet, Chamfer, Shell, FeatureHistory."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .mesh import Mesh
from .parameters import ParameterStore
from .features_core import (
    FeatureValidationError,
    validate_fillet_data,
    validate_chamfer_data,
    validate_history_data,
    _new_id,
    _resolve_value,
)
from .shell_feature import ShellFeature  # noqa: F401


class FilletFeature:
    def __init__(self, radius: float | str = 1.0, name: str = "Fillet", edges=None, operation: str = "modify", metadata=None, id=None):
        self.id = id or _new_id("fillet")
        self.type = "fillet"
        self.name = name
        self.radius = radius
        self.edges = edges or []
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data = {"id": self.id, "type": self.type, "name": self.name, "radius": self.radius, "edges": self.edges, "operation": self.operation}
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_fillet_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "FilletFeature":
        validate_fillet_data(data)
        return cls(radius=data["radius"], name=data.get("name", "Fillet"), edges=data.get("edges"), operation=data.get("operation", "modify"), metadata=data.get("metadata"), id=data.get("id"))

    def resolved_radius(self, parameters=None) -> float:
        return _resolve_value(self.radius, parameters, 1.0)

    def apply_to_mesh(self, mesh: Mesh, parameters=None) -> Mesh:
        return mesh


class ChamferFeature:
    def __init__(self, distance: float | str = 1.0, name: str = "Chamfer", edges=None, mode: str = "equal", secondary=None, operation: str = "modify", metadata=None, id=None):
        self.id = id or _new_id("chamfer")
        self.type = "chamfer"
        self.name = name
        self.distance = distance
        self.edges = edges or []
        self.mode = mode
        self.secondary = secondary
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data = {"id": self.id, "type": self.type, "name": self.name, "distance": self.distance, "edges": self.edges, "mode": self.mode, "operation": self.operation}
        if self.secondary is not None:
            data["secondary"] = self.secondary
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_chamfer_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "ChamferFeature":
        validate_chamfer_data(data)
        return cls(distance=data["distance"], name=data.get("name", "Chamfer"), edges=data.get("edges"), mode=data.get("mode", "equal"), secondary=data.get("secondary"), operation=data.get("operation", "modify"), metadata=data.get("metadata"), id=data.get("id"))

    def apply_to_mesh(self, mesh: Mesh, parameters=None) -> Mesh:
        return mesh


class FeatureHistory:
    def __init__(self, features=None, name: str = "Feature History", rollback_marker=None, metadata=None, id=None):
        self.id = id or _new_id("hist")
        self.name = name
        self.features: List[dict] = features or []
        self.rollback_marker = rollback_marker
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data = {"id": self.id, "name": self.name, "features": self.features}
        if self.rollback_marker is not None:
            data["rollback_marker"] = self.rollback_marker
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_history_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureHistory":
        validate_history_data(data)
        return cls(features=data.get("features"), name=data.get("name", "Feature History"), rollback_marker=data.get("rollback_marker"), metadata=data.get("metadata"), id=data.get("id"))

    def add(self, feature_dict: dict) -> None:
        self.features.append(feature_dict)
        self.validate()

    def active_features(self) -> List[dict]:
        if self.rollback_marker is None:
            return list(self.features)
        marker = max(0, min(self.rollback_marker, len(self.features)))
        return self.features[:marker]

    def recompute_meshes(self, sketches: dict, parameters=None) -> Dict[str, Mesh]:
        from .features import ExtrudeFeature, RevolveFeature, HoleFeature
        result: Dict[str, Mesh] = {}
        for fdict in self.active_features():
            ftype = fdict.get("type")
            fid = fdict.get("id", "feat")
            try:
                if ftype == "extrude":
                    feat = ExtrudeFeature.from_dict(fdict)
                    sketch = sketches.get(feat.sketch_id)
                    if sketch:
                        result[fid] = feat.generate_mesh(sketch, parameters)
                elif ftype == "revolve":
                    feat = RevolveFeature.from_dict(fdict)
                    sketch = sketches.get(feat.sketch_id)
                    if sketch:
                        result[fid] = feat.generate_mesh(sketch, parameters)
                elif ftype == "hole":
                    feat = HoleFeature.from_dict(fdict)
                    result[fid] = feat.generate_mesh(parameters)
            except Exception:
                continue
        return result
