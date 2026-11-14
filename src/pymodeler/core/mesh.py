"""Mesh data model with JSON Schema validation."""

from __future__ import annotations

import json
import math
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

    def extrude_faces(
        self,
        face_indices: Optional[Sequence[int]] = None,
        direction: Sequence[float] = (0.0, 0.0, 1.0),
        distance: float = 1.0,
    ) -> None:
        """Extrude selected faces (or all faces if None) along a direction.

        Implements a simple region extrude:
        - Boundary edges of the selection become side faces.
        - Selected faces are duplicated and translated.
        - Internal edges are not extruded as walls.

        Modifies the mesh in place. Always re-validates.
        """
        import numpy as np

        if not self.faces:
            return

        if face_indices is None:
            face_indices = list(range(len(self.faces)))
        else:
            face_indices = [int(i) for i in face_indices if 0 <= i < len(self.faces)]
            if not face_indices:
                return

        selected = set(face_indices)
        dir_vec = np.asarray(direction, dtype=float)
        norm = np.linalg.norm(dir_vec)
        if norm < 1e-8:
            dir_vec = np.array([0.0, 0.0, 1.0])
        else:
            dir_vec = dir_vec / norm
        offset = dir_vec * float(distance)

        # Collect all unique vertices used by selected faces
        selected_verts = set()
        for fi in face_indices:
            selected_verts.update(self.faces[fi])

        # Build edge -> list of face indices that use it (within selection)
        from collections import defaultdict
        edge_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
        for fi in face_indices:
            face = self.faces[fi]
            n = len(face)
            for i in range(n):
                a, b = face[i], face[(i + 1) % n]
                key = (min(a, b), max(a, b))
                edge_faces[key].append(fi)

        # Boundary edges: appear in exactly one selected face
        boundary_edges = [e for e, faces in edge_faces.items() if len(faces) == 1]

        # Map old vertex index -> new extruded vertex index
        vert_map: dict[int, int] = {}
        new_vertices = [list(v) for v in self.vertices]  # copy
        for vi in sorted(selected_verts):
            old = np.asarray(self.vertices[vi])
            new_pos = (old + offset).tolist()
            vert_map[vi] = len(new_vertices)
            new_vertices.append(new_pos)

        # New faces: extruded copies of selected faces (reversed winding for consistent normals if needed)
        new_faces = [list(f) for f in self.faces]
        for fi in face_indices:
            old_face = self.faces[fi]
            extruded = [vert_map[vi] for vi in old_face]
            # Reverse to keep outward normal roughly consistent when extruding "out"
            new_faces.append(list(reversed(extruded)))

        # Side faces for each boundary edge
        for a, b in boundary_edges:
            # Determine orientation from the face that owns the edge
            owning = edge_faces[(a, b)][0]
            face = self.faces[owning]
            # Find the directed edge in the face
            n = len(face)
            for i in range(n):
                if face[i] == a and face[(i + 1) % n] == b:
                    # directed a -> b
                    na, nb = vert_map[a], vert_map[b]
                    # side quad: a, b, nb, na  (or reverse depending on desired winding)
                    new_faces.append([a, b, nb, na])
                    break
                elif face[i] == b and face[(i + 1) % n] == a:
                    # directed b -> a
                    na, nb = vert_map[a], vert_map[b]
                    new_faces.append([b, a, na, nb])
                    break

        self.vertices = new_vertices
        self.faces = new_faces
        # Clear optional derived data so it is recomputed later if needed
        self.edges = None
        self.normals = None
        self.validate()

    def compute_face_normal(self, face_index: int) -> list[float]:
        """Return approximate face normal (Newell / cross product of first triangle)."""
        face = self.faces[face_index]
        if len(face) < 3:
            return [0.0, 0.0, 1.0]
        v0 = self.vertices[face[0]]
        v1 = self.vertices[face[1]]
        v2 = self.vertices[face[2]]
        e1 = [v1[i] - v0[i] for i in range(3)]
        e2 = [v2[i] - v0[i] for i in range(3)]
        # Cross product
        n = [
            e1[1] * e2[2] - e1[2] * e2[1],
            e1[2] * e2[0] - e1[0] * e2[2],
            e1[0] * e2[1] - e1[1] * e2[0],
        ]
        length = math.sqrt(sum(c * c for c in n)) or 1.0
        return [c / length for c in n]


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


def create_plane(
    size: float = 2.0,
    name: str = "Plane",
    subdivisions: int = 1,
) -> Mesh:
    """Create a flat plane in the XY plane (Z=0), centered at origin.

    subdivisions >= 1 divides each side into that many segments.
    """
    if subdivisions < 1:
        raise ValueError("subdivisions must be >= 1")
    half = size / 2.0
    step = size / subdivisions
    vertices: List[List[float]] = []
    for j in range(subdivisions + 1):
        y = -half + j * step
        for i in range(subdivisions + 1):
            x = -half + i * step
            vertices.append([x, y, 0.0])

    faces: List[List[int]] = []
    cols = subdivisions + 1
    for j in range(subdivisions):
        for i in range(subdivisions):
            v0 = j * cols + i
            v1 = v0 + 1
            v2 = v0 + cols + 1
            v3 = v0 + cols
            faces.append([v0, v1, v2, v3])

    return Mesh(vertices=vertices, faces=faces, name=name)


def create_sphere(
    radius: float = 1.0,
    segments: int = 32,
    rings: int = 16,
    name: str = "Sphere",
) -> Mesh:
    """Create a UV sphere centered at origin.

    segments: longitudinal divisions (around Y)
    rings: latitudinal divisions (from south to north pole, excluding poles)
    """
    if segments < 3 or rings < 2:
        raise ValueError("segments >= 3 and rings >= 2 required")

    vertices: List[List[float]] = []
    # South pole
    vertices.append([0.0, -radius, 0.0])
    # Intermediate rings
    for ring in range(1, rings):
        phi = math.pi * ring / rings  # 0 at north? Wait: from south
        # phi from 0 (south) to pi (north), but we start after south pole
        y = -radius * math.cos(phi)
        r_xz = radius * math.sin(phi)
        for seg in range(segments):
            theta = 2.0 * math.pi * seg / segments
            x = r_xz * math.cos(theta)
            z = r_xz * math.sin(theta)
            vertices.append([x, y, z])
    # North pole
    vertices.append([0.0, radius, 0.0])

    faces: List[List[int]] = []
    # South pole fan (triangles)
    south = 0
    first_ring_start = 1
    for seg in range(segments):
        next_seg = (seg + 1) % segments
        faces.append([south, first_ring_start + next_seg, first_ring_start + seg])

    # Middle quads
    for ring in range(rings - 2):
        ring_start = 1 + ring * segments
        next_ring_start = ring_start + segments
        for seg in range(segments):
            next_seg = (seg + 1) % segments
            v0 = ring_start + seg
            v1 = ring_start + next_seg
            v2 = next_ring_start + next_seg
            v3 = next_ring_start + seg
            faces.append([v0, v1, v2, v3])

    # North pole fan
    north = len(vertices) - 1
    last_ring_start = 1 + (rings - 2) * segments
    for seg in range(segments):
        next_seg = (seg + 1) % segments
        faces.append([last_ring_start + seg, last_ring_start + next_seg, north])

    return Mesh(vertices=vertices, faces=faces, name=name)


def create_cylinder(
    radius: float = 1.0,
    height: float = 2.0,
    segments: int = 32,
    name: str = "Cylinder",
    capped: bool = True,
) -> Mesh:
    """Create a cylinder along the Y axis, centered at origin."""
    if segments < 3:
        raise ValueError("segments >= 3 required")

    half_h = height / 2.0
    vertices: List[List[float]] = []
    # Bottom ring
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        vertices.append([x, -half_h, z])
    # Top ring
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        vertices.append([x, half_h, z])

    faces: List[List[int]] = []
    # Side quads
    for i in range(segments):
        next_i = (i + 1) % segments
        v0 = i                  # bottom
        v1 = next_i
        v2 = segments + next_i  # top
        v3 = segments + i
        faces.append([v0, v1, v2, v3])

    if capped:
        # Bottom center
        bottom_center = len(vertices)
        vertices.append([0.0, -half_h, 0.0])
        # Top center
        top_center = len(vertices)
        vertices.append([0.0, half_h, 0.0])

        # Bottom fan (winding outward or consistent)
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([bottom_center, next_i, i])
        # Top fan
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([top_center, segments + i, segments + next_i])

    return Mesh(vertices=vertices, faces=faces, name=name)


def create_cone(
    radius: float = 1.0,
    height: float = 2.0,
    segments: int = 32,
    name: str = "Cone",
    capped: bool = True,
) -> Mesh:
    """Create a cone along the Y axis, base at -height/2, tip at +height/2."""
    if segments < 3:
        raise ValueError("segments >= 3 required")

    half_h = height / 2.0
    vertices: List[List[float]] = []
    # Base ring
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        vertices.append([x, -half_h, z])
    # Tip
    tip = len(vertices)
    vertices.append([0.0, half_h, 0.0])

    faces: List[List[int]] = []
    # Side triangles
    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([i, next_i, tip])

    if capped:
        # Base center
        base_center = len(vertices)
        vertices.append([0.0, -half_h, 0.0])
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([base_center, next_i, i])

    return Mesh(vertices=vertices, faces=faces, name=name)
