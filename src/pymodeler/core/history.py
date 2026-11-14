"""Undo/Redo command stack using the command pattern.

Supports reversing add, delete, and transform operations on the scene.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .scene import Scene, SceneObject, Transform


class Command(ABC):
    """Base class for undoable commands."""

    @abstractmethod
    def execute(self) -> None:
        """Perform the command."""
        ...

    @abstractmethod
    def undo(self) -> None:
        """Reverse the command."""
        ...


class CommandStack:
    """Stack of commands with undo/redo support.

    Limited history depth to avoid unbounded memory growth.
    """

    def __init__(self, limit: int = 100) -> None:
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self.limit = limit

    def push(self, command: Command) -> None:
        """Execute the command and record it for undo."""
        command.execute()
        self._undo_stack.append(command)
        if len(self._undo_stack) > self.limit:
            self._undo_stack.pop(0)
        # New command clears the redo stack
        self._redo_stack.clear()

    def undo(self) -> Optional[Command]:
        """Undo the most recent command. Returns the command or None."""
        if not self._undo_stack:
            return None
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        return command

    def redo(self) -> Optional[Command]:
        """Redo the most recently undone command. Returns the command or None."""
        if not self._redo_stack:
            return None
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        return command

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()


class AddObjectCommand(Command):
    """Add a SceneObject to the scene."""

    def __init__(self, scene: Scene, obj: SceneObject) -> None:
        self.scene = scene
        self.obj = obj

    def execute(self) -> None:
        self.scene.add_object(self.obj)

    def undo(self) -> None:
        self.scene.remove_object(self.obj.name)


class RemoveObjectCommand(Command):
    """Remove a SceneObject from the scene (preserves order on undo)."""

    def __init__(self, scene: Scene, obj: SceneObject) -> None:
        self.scene = scene
        self.obj = obj
        self._index: Optional[int] = None

    def execute(self) -> None:
        for i, o in enumerate(self.scene.objects):
            if o.name == self.obj.name:
                self._index = i
                self.scene.deselect(o)
                self.scene.objects.pop(i)
                return
        raise ValueError(f"Object {self.obj.name!r} not found in scene")

    def undo(self) -> None:
        if self._index is not None:
            self.scene.objects.insert(self._index, self.obj)
        else:
            self.scene.add_object(self.obj)


class SetTransformCommand(Command):
    """Set a new transform on a SceneObject (stores previous state)."""

    def __init__(self, obj: SceneObject, new_transform: Transform) -> None:
        self.obj = obj
        # Deep-copy current transform
        self._old = Transform(
            location=list(obj.transform.location),
            rotation=list(obj.transform.rotation),
            scale=list(obj.transform.scale),
        )
        # Copy the incoming transform so later mutations don't affect history
        self._new = Transform(
            location=list(new_transform.location),
            rotation=list(new_transform.rotation),
            scale=list(new_transform.scale),
        )

    def execute(self) -> None:
        self.obj.transform = self._new

    def undo(self) -> None:
        self.obj.transform = self._old


class ExtrudeMeshCommand(Command):
    """Extrude faces on a SceneObject's mesh. Stores previous mesh state for undo."""

    def __init__(
        self,
        obj: SceneObject,
        face_indices: Optional[list[int]] = None,
        direction: list[float] | tuple[float, float, float] = (0.0, 0.0, 1.0),
        distance: float = 1.0,
    ) -> None:
        self.obj = obj
        self.face_indices = list(face_indices) if face_indices is not None else None
        self.direction = list(direction)
        self.distance = float(distance)
        # Snapshot current mesh for undo
        self._old_vertices = [list(v) for v in obj.mesh.vertices]
        self._old_faces = [list(f) for f in obj.mesh.faces]
        self._old_edges = obj.mesh.edges
        self._old_normals = obj.mesh.normals

    def execute(self) -> None:
        self.obj.mesh.extrude_faces(
            face_indices=self.face_indices,
            direction=self.direction,
            distance=self.distance,
        )

    def undo(self) -> None:
        self.obj.mesh.vertices = self._old_vertices
        self.obj.mesh.faces = self._old_faces
        self.obj.mesh.edges = self._old_edges
        self.obj.mesh.normals = self._old_normals
        self.obj.mesh.validate()
