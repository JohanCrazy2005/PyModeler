"""Additional features: Fillet, Chamfer, FeatureHistory."""
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
    ExtrudeFeature,
    RevolveFeature,
    HoleFeature,
)

class FilletFeature:
    """Parametric Fillet feature stub.

    Stores radius and optional edge selection. Full rolling-ball mesh fillet is deferred.
    generate_mesh returns a small placeholder sphere whose radius matches the fillet radius
    so the feature is visible in the timeline / recompute path.
    """

    def __init__(
        self,
        radius: float | str = 1.0,
        name: str = "Fillet",
        edges: Optional[list] = None,
        operation: str = "modify",
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("fillet")
        self.type = "fillet"
        self.name = name
        self.radius = radius
        self.edges = edges or []
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "radius": self.radius,
            "edges": self.edges,
            "operation": self.operation,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_fillet_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "FilletFeature":
        validate_fillet_data(data)
        return cls(
            radius=data["radius"],
            name=data.get("name", "Fillet"),
            edges=data.get("edges", []),
            operation=data.get("operation", "modify"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_radius(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.radius, parameters, 1.0)

    def generate_mesh(self, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Placeholder mesh for timeline visibility when no base body is available."""
        r = self.resolved_radius(parameters)
        if r <= 0:
            raise FeatureValidationError("Fillet radius must be positive")
        from .mesh import create_sphere
        return create_sphere(radius=r, name=self.id)

    def apply_to_mesh(self, base: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Apply a basic multi-segment edge bevel approximating a fillet on *base*."""
        r = self.resolved_radius(parameters)
        if r <= 0:
            raise FeatureValidationError("Fillet radius must be positive")
        edges = self.edges if self.edges else None
        # segments=4 gives a coarse rounded look
        return base.bevel_edges(edges=edges, amount=r, segments=4, name=f"{base.name}_fillet")


class ChamferFeature:
    """Parametric Chamfer feature stub.

    Stores distance and optional edge selection. Full edge bevel mesh is deferred.
    generate_mesh returns a small placeholder cone of the chamfer distance.
    """

    def __init__(
        self,
        distance: float | str = 1.0,
        name: str = "Chamfer",
        edges: Optional[list] = None,
        operation: str = "modify",
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("chamfer")
        self.type = "chamfer"
        self.name = name
        self.distance = distance
        self.edges = edges or []
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "distance": self.distance,
            "edges": self.edges,
            "operation": self.operation,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_chamfer_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "ChamferFeature":
        validate_chamfer_data(data)
        return cls(
            distance=data["distance"],
            name=data.get("name", "Chamfer"),
            edges=data.get("edges", []),
            operation=data.get("operation", "modify"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_distance(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.distance, parameters, 1.0)

    def generate_mesh(self, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Placeholder mesh for timeline visibility when no base body is available."""
        d = self.resolved_distance(parameters)
        if d <= 0:
            raise FeatureValidationError("Chamfer distance must be positive")
        from .mesh import create_cone
        mesh = create_cone(radius=d, height=d * 0.5, name=self.id)
        return mesh

    def apply_to_mesh(self, base: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Apply a basic single-segment edge bevel (flat chamfer) on *base*."""
        d = self.resolved_distance(parameters)
        if d <= 0:
            raise FeatureValidationError("Chamfer distance must be positive")
        edges = self.edges if self.edges else None
        return base.bevel_edges(edges=edges, amount=d, segments=1, name=f"{base.name}_chamfer")


class FeatureHistory:
    """Ordered timeline of features with rollback support."""

    def __init__(
        self,
        name: str = "Feature History",
        features: Optional[List[dict]] = None,
        rollback_marker: Optional[int] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("hist")
        self.name = name
        self.features: List[dict] = features or []
        self.rollback_marker = rollback_marker
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "features": self.features,
        }
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
        return cls(
            name=data.get("name", "Feature History"),
            features=data.get("features", []),
            rollback_marker=data.get("rollback_marker"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def add_extrude(self, feat: ExtrudeFeature) -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def add_revolve(self, feat: RevolveFeature) -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def add_hole(self, feat: "HoleFeature") -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def add_fillet(self, feat: "FilletFeature") -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def add_chamfer(self, feat: "ChamferFeature") -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def active_features(self) -> List[dict]:
        if self.rollback_marker is None:
            return list(self.features)
        return list(self.features[: self.rollback_marker + 1])

    def recompute_meshes(self, sketches, params=None):
        result = {}
        for fdict in self.active_features():
            fid = fdict.get("id", "feat")
            try:
                if fdict.get("type") == "extrude":
                    feat = ExtrudeFeature.from_dict(fdict)
                    sk = sketches.get(feat.sketch_id) if sketches else None
                    if sk is not None:
                        result[fid] = feat.generate_mesh(sk, params)
                elif fdict.get("type") == "revolve":
                    feat = RevolveFeature.from_dict(fdict)
                    sk = sketches.get(feat.sketch_id) if sketches else None
                    if sk is not None:
                        result[fid] = feat.generate_mesh(sk, params)
                elif fdict.get("type") == "hole":
                    feat = HoleFeature.from_dict(fdict)
                    result[fid] = feat.generate_mesh(params)
                elif fdict.get("type") == "fillet":
                    feat = FilletFeature.from_dict(fdict)
                    result[fid] = feat.generate_mesh(params)
                elif fdict.get("type") == "chamfer":
                    feat = ChamferFeature.from_dict(fdict)
                    result[fid] = feat.generate_mesh(params)
            except Exception:
                from .mesh import create_cube
                result[fid] = create_cube(size=1.0, name=fid)
        return result
