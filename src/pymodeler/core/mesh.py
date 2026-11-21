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
        individual: bool = False,
        use_per_face_normals: bool = False,
    ) -> None:
        """Extrude selected faces (or all faces if None).

        Parameters
        ----------
        face_indices : optional list of face indices to extrude. None = all faces.
        direction : shared extrusion direction (normalized). Ignored when
            use_per_face_normals is True.
        distance : extrusion distance.
        individual : if True, each face is extruded independently (every edge
            becomes a side wall). If False, region extrude: only boundary edges
            of the selection produce side faces.
        use_per_face_normals : if True, each face is extruded along its own
            computed normal (overrides direction). Best combined with individual=True.

        Implements a simple region or individual extrude:
        - Boundary (or all) edges become side faces.
        - Selected faces are duplicated and translated.
        - Internal edges of a region are not extruded as walls.

        Modifies the mesh in place. Always re-validates.
        """
        import numpy as np
        from collections import defaultdict

        if not self.faces:
            return

        if face_indices is None:
            face_indices = list(range(len(self.faces)))
        else:
            face_indices = [int(i) for i in face_indices if 0 <= i < len(self.faces)]
            if not face_indices:
                return

        # For individual mode we process faces one-by-one so each has its own sides.
        # For region mode we treat the whole selection as one region.
        if individual:
            # Process in reverse order so earlier indices stay valid while we grow the mesh
            for fi in reversed(face_indices):
                self._extrude_region(
                    [fi],
                    direction,
                    distance,
                    use_per_face_normals,
                )
            return

        self._extrude_region(face_indices, direction, distance, use_per_face_normals)

    def _extrude_region(
        self,
        face_indices: list[int],
        direction: Sequence[float],
        distance: float,
        use_per_face_normals: bool,
    ) -> None:
        """Internal helper that extrudes a contiguous region (or single face)."""
        import numpy as np
        from collections import defaultdict

        selected = set(face_indices)
        dir_vec = np.asarray(direction, dtype=float)
        norm = np.linalg.norm(dir_vec)
        if norm < 1e-8:
            dir_vec = np.array([0.0, 0.0, 1.0])
        else:
            dir_vec = dir_vec / norm

        # Collect vertices used by the selected faces
        selected_verts = set()
        for fi in face_indices:
            selected_verts.update(self.faces[fi])

        # Build edge -> list of face indices that use it (within selection)
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
        # When use_per_face_normals we may need per-face offsets, but for simplicity
        # we still share vertices within the region and use average normal if requested.
        if use_per_face_normals and len(face_indices) > 1:
            # Average the normals of the region
            normals = [self.compute_face_normal(fi) for fi in face_indices]
            avg = np.mean(normals, axis=0)
            length = np.linalg.norm(avg)
            dir_vec = avg / length if length > 1e-8 else np.array([0.0, 0.0, 1.0])
        elif use_per_face_normals and len(face_indices) == 1:
            n = self.compute_face_normal(face_indices[0])
            dir_vec = np.asarray(n, dtype=float)

        offset = dir_vec * float(distance)

        vert_map: dict[int, int] = {}
        new_vertices = [list(v) for v in self.vertices]
        for vi in sorted(selected_verts):
            old = np.asarray(self.vertices[vi])
            new_pos = (old + offset).tolist()
            vert_map[vi] = len(new_vertices)
            new_vertices.append(new_pos)

        # New faces: extruded copies of selected faces (reversed winding for consistent normals)
        new_faces = [list(f) for f in self.faces]
        for fi in face_indices:
            old_face = self.faces[fi]
            extruded = [vert_map[vi] for vi in old_face]
            # Reverse to keep outward normal roughly consistent when extruding "out"
            new_faces.append(list(reversed(extruded)))

        # Side faces for each boundary edge – improved winding
        for a, b in boundary_edges:
            owning = edge_faces[(a, b)][0]
            face = self.faces[owning]
            n = len(face)
            # Find the directed edge in the owning face
            directed = None
            for i in range(n):
                if face[i] == a and face[(i + 1) % n] == b:
                    directed = (a, b)
                    break
                elif face[i] == b and face[(i + 1) % n] == a:
                    directed = (b, a)
                    break
            if directed is None:
                continue
            da, db = directed
            na, nb = vert_map[da], vert_map[db]
            # Side quad: try the conventional order, then flip if the normal
            # does not point roughly outward relative to the extrusion direction.
            candidate = [da, db, nb, na]
            # Compute a quick normal of the candidate (using first three verts)
            c0 = np.asarray(new_vertices[candidate[0]])
            c1 = np.asarray(new_vertices[candidate[1]])
            c2 = np.asarray(new_vertices[candidate[2]])
            sn = np.cross(c1 - c0, c2 - c0)
            # Prefer the orientation whose normal has positive dot with dir_vec
            if np.dot(sn, dir_vec) < 0:
                candidate = [da, na, nb, db]
            new_faces.append(candidate)

        self.vertices = new_vertices
        self.faces = new_faces
        # Clear optional derived data so it is recomputed later if needed
        self.edges = None
        self.normals = None
        self.validate()

    def inset_faces(
        self,
        face_indices: Optional[Sequence[int]] = None,
        thickness: float = 0.2,
        depth: float = 0.0,
        individual: bool = True,
    ) -> None:
        """Inset selected faces (or all faces if None).

        Parameters
        ----------
        face_indices : optional list of face indices. None = all faces.
        thickness : fraction in [0, 1] of the way toward the face centroid.
            0 = no inset, 1 = collapse to centroid.
        depth : optional translation of the new inset face along its normal.
        individual : if True (default for this basic implementation), each face
            is inset independently. Region mode is planned for a later increment.

        Creates new vertices for the inset face(s), replaces the original face
        with the smaller one, and adds border quads. Modifies the mesh in place.
        Always re-validates.
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

        thickness = max(0.0, min(1.0, float(thickness)))
        depth = float(depth)

        # Process in reverse so earlier indices remain valid while we grow the mesh
        for fi in reversed(face_indices):
            self._inset_single_face(fi, thickness, depth)

    def _inset_single_face(self, face_index: int, thickness: float, depth: float) -> None:
        """Inset a single face by creating new vertices toward its centroid."""
        import numpy as np

        face = self.faces[face_index]
        if len(face) < 3:
            return

        verts = [np.asarray(self.vertices[vi], dtype=float) for vi in face]
        centroid = np.mean(verts, axis=0)

        # Optional depth along normal
        normal = np.asarray(self.compute_face_normal(face_index), dtype=float)
        depth_offset = normal * depth

        # Create new inset vertices
        new_vert_indices = []
        for v in verts:
            inset_pos = v + thickness * (centroid - v) + depth_offset
            new_idx = len(self.vertices)
            self.vertices.append(inset_pos.tolist())
            new_vert_indices.append(new_idx)

        # Border quads (one per edge)
        n = len(face)
        new_faces = []
        for i in range(n):
            a = face[i]
            b = face[(i + 1) % n]
            na = new_vert_indices[i]
            nb = new_vert_indices[(i + 1) % n]
            # Quad: original edge then inset edge (winding consistent with original)
            new_faces.append([a, b, nb, na])

        # Replace the original face with the inset face (same winding)
        self.faces[face_index] = list(new_vert_indices)

        # Append border faces
        self.faces.extend(new_faces)

        # Clear derived data
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

    def get_unique_edges(self) -> list[tuple[int, int]]:
        """Return sorted unique edges as (min_idx, max_idx) pairs."""
        edges = set()
        for face in self.faces:
            n = len(face)
            for i in range(n):
                a, b = face[i], face[(i + 1) % n]
                edges.add((min(a, b), max(a, b)))
        return sorted(edges)

    def edge_face_map(self) -> dict[tuple[int, int], list[int]]:
        """Map each unique edge to the list of face indices that contain it."""
        from collections import defaultdict
        ef: dict[tuple[int, int], list[int]] = defaultdict(list)
        for fi, face in enumerate(self.faces):
            n = len(face)
            for i in range(n):
                a, b = face[i], face[(i + 1) % n]
                key = (min(a, b), max(a, b))
                ef[key].append(fi)
        return dict(ef)

    def bevel_edges(
        self,
        edges: Optional[Sequence] = None,
        amount: float = 0.1,
        segments: int = 1,
        amount2: Optional[float] = None,
        name: Optional[str] = None,
        cleanup: bool = True,
    ) -> "Mesh":
        """Improved edge bevel / chamfer approximation.

        Creates proper offset vertices using adjacent-face normals so the
        chamfer faces lie approximately in the bisector plane of the edge.
        Supports equal-distance (amount) and a second distance (amount2).
        segments > 1 inserts intermediate vertices for a coarse multi-segment
        fillet look. At vertices where multiple beveled edges meet, a simple
        corner fan is added. Optional cleanup removes degenerate faces and
        merges near-coincident vertices.
        """
        import numpy as np
        from collections import defaultdict

        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount2 is not None and amount2 <= 0:
            raise ValueError("amount2 must be positive")
        if segments < 1:
            segments = 1

        new_verts = [list(map(float, v)) for v in self.vertices]
        new_faces = [list(f) for f in self.faces]
        unique = self.get_unique_edges()
        ef_map = self.edge_face_map()

        selected: list[tuple[int, int]] = []
        if edges is None:
            selected = unique
        else:
            for e in edges:
                if isinstance(e, (list, tuple)) and len(e) == 2:
                    selected.append((min(int(e[0]), int(e[1])), max(int(e[0]), int(e[1]))))
                elif isinstance(e, int) and 0 <= e < len(unique):
                    selected.append(unique[e])

        d1 = float(amount)
        d2 = float(amount2) if amount2 is not None else d1
        # Use average of the two distances for the primary offset magnitude
        offset_mag = (d1 + d2) * 0.5

        # Track new offset vertices created for each original vertex so we can
        # build corner fans later.
        corner_offsets: dict[int, list[int]] = defaultdict(list)

        for a, b in selected:
            va = np.asarray(new_verts[a], dtype=float)
            vb = np.asarray(new_verts[b], dtype=float)
            edge_dir = vb - va
            edge_len = np.linalg.norm(edge_dir)
            if edge_len < 1e-8:
                continue
            edge_dir = edge_dir / edge_len

            # Average normal of adjacent faces (or a fallback)
            face_indices = ef_map.get((a, b), [])
            normals = []
            for fi in face_indices:
                n = np.asarray(self.compute_face_normal(fi), dtype=float)
                if np.linalg.norm(n) > 1e-8:
                    normals.append(n)
            if normals:
                avg_n = np.mean(normals, axis=0)
                avg_n /= np.linalg.norm(avg_n) or 1.0
            else:
                avg_n = np.array([0.0, 0.0, 1.0])

            # Perpendicular direction in the plane of the average normal
            perp = np.cross(edge_dir, avg_n)
            perp_len = np.linalg.norm(perp)
            if perp_len < 1e-8:
                # Fallback perpendicular
                perp = np.cross(edge_dir, np.array([0.0, 1.0, 0.0]))
                if np.linalg.norm(perp) < 1e-8:
                    perp = np.cross(edge_dir, np.array([1.0, 0.0, 0.0]))
            perp = perp / (np.linalg.norm(perp) or 1.0)

            # Primary offset vertices (equal-distance style)
            off_a = va + perp * offset_mag
            off_b = vb + perp * offset_mag
            na_idx = len(new_verts)
            new_verts.append(off_a.tolist())
            nb_idx = len(new_verts)
            new_verts.append(off_b.tolist())
            corner_offsets[a].append(na_idx)
            corner_offsets[b].append(nb_idx)

            # Chamfer face (quad)
            new_faces.append([a, b, nb_idx, na_idx])

            # Extra segments for a coarse fillet approximation
            if segments > 1:
                for s in range(1, segments):
                    frac = s / float(segments)
                    # Interpolate between original edge and the offset line
                    mid_a = va + perp * (offset_mag * frac)
                    mid_b = vb + perp * (offset_mag * frac)
                    ma_idx = len(new_verts)
                    new_verts.append(mid_a.tolist())
                    mb_idx = len(new_verts)
                    new_verts.append(mid_b.tolist())
                    # Connect previous to this segment
                    prev_a = na_idx if s == 1 else ma_idx - 2
                    prev_b = nb_idx if s == 1 else mb_idx - 2
                    new_faces.append([prev_a, prev_b, mb_idx, ma_idx])

        # Simple corner fans: for each original vertex that received multiple
        # offset vertices, create a triangle fan from the original vertex.
        for orig_idx, offs in corner_offsets.items():
            if len(offs) >= 2:
                # Sort offsets roughly around the vertex for better fan order
                center = np.asarray(new_verts[orig_idx], dtype=float)
                def angle_key(oid: int) -> float:
                    v = np.asarray(new_verts[oid], dtype=float) - center
                    return math.atan2(v[1], v[0])
                sorted_offs = sorted(set(offs), key=angle_key)
                for i in range(len(sorted_offs)):
                    j = (i + 1) % len(sorted_offs)
                    # Triangle: original -> offset_i -> offset_j
                    new_faces.append([orig_idx, sorted_offs[i], sorted_offs[j]])

        result = Mesh(
            vertices=new_verts,
            faces=new_faces,
            name=name or f"{self.name}_bevel",
        )

        if cleanup:
            result = result._cleanup_mesh()
        return result

    def _cleanup_mesh(self, tol: float = 1e-6) -> "Mesh":
        """Remove degenerate faces and merge near-coincident vertices.

        Lightweight manifold-oriented cleanup used after bevel / other ops.
        """
        import numpy as np

        verts = [list(map(float, v)) for v in self.vertices]
        faces = [list(f) for f in self.faces]

        # Merge vertices that are closer than tol
        # Simple O(n^2) is fine for the small meshes we produce here
        remap: dict[int, int] = {}
        kept: list[list[float]] = []
        for i, v in enumerate(verts):
            if i in remap:
                continue
            nv = np.asarray(v, dtype=float)
            new_idx = len(kept)
            kept.append(v)
            remap[i] = new_idx
            for j in range(i + 1, len(verts)):
                if j in remap:
                    continue
                if np.linalg.norm(nv - np.asarray(verts[j], dtype=float)) < tol:
                    remap[j] = new_idx

        # Rebuild faces, dropping degenerates
        new_faces: list[list[int]] = []
        for face in faces:
            remapped = [remap.get(vi, vi) for vi in face]
            # Drop if fewer than 3 unique verts or zero area
            uniq = []
            for vi in remapped:
                if vi not in uniq:
                    uniq.append(vi)
            if len(uniq) < 3:
                continue
            # Quick area check
            if len(uniq) >= 3:
                v0 = np.asarray(kept[uniq[0]])
                v1 = np.asarray(kept[uniq[1]])
                v2 = np.asarray(kept[uniq[2]])
                area = 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0))
                if area < tol * 10:
                    continue
            new_faces.append(remapped)

        return Mesh(
            vertices=kept,
            faces=new_faces,
            name=self.name,
        )


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
