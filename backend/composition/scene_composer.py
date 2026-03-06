"""
Scene composer — assembles multiple meshes into a single 3D scene.

Supports manual placement and automatic bounding-box-based layout so
objects don't overlap.  Exports the composed scene as a GLB file.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import trimesh
import trimesh.transformations as tf

logger = logging.getLogger(__name__)


@dataclass
class SceneObject:
    """A single mesh entry in the scene with its placement metadata."""

    mesh: trimesh.Trimesh
    name: str
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    scale: float = 1.0


class SceneComposer:
    """
    Composes multiple meshes into a single trimesh.Scene.

    Typical usage
    -------------
    >>> composer = SceneComposer()
    >>> composer.add_object(chair_mesh, "chair")
    >>> composer.add_object(table_mesh, "table")
    >>> composer.auto_layout(spacing=0.05)
    >>> composer.export("scene.glb")

    Objects are added by reference; the original meshes are *not* mutated.
    Copies are made when composing or exporting.
    """

    def __init__(self) -> None:
        self._objects: list[SceneObject] = []

    # ------------------------------------------------------------------
    # Object management
    # ------------------------------------------------------------------

    def add_object(
        self,
        mesh: trimesh.Trimesh,
        name: str,
        position: Optional[np.ndarray] = None,
        scale: float = 1.0,
    ) -> None:
        """
        Add *mesh* to the scene.

        Parameters
        ----------
        mesh:
            Source mesh (not mutated; a copy is made on compose/export).
        name:
            Unique name for the geometry in the scene graph.
        position:
            World-space origin (centre) of the object.  Defaults to origin.
        scale:
            Uniform scale factor applied before placement.
        """
        pos = position if position is not None else np.zeros(3)
        self._objects.append(SceneObject(mesh=mesh, name=name, position=pos, scale=scale))
        logger.info(
            "Added '%s' — scale=%.2f, position=%s", name, scale, pos.tolist()
        )

    def remove_object(self, name: str) -> None:
        """Remove the first object whose name matches *name*."""
        before = len(self._objects)
        self._objects = [o for o in self._objects if o.name != name]
        if len(self._objects) < before:
            logger.info("Removed object '%s' from scene.", name)
        else:
            logger.warning("No object named '%s' found in scene.", name)

    def clear(self) -> None:
        self._objects.clear()
        logger.debug("Scene cleared.")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def auto_layout(self, spacing: float = 0.1, axis: int = 0) -> None:
        """
        Automatically arrange all objects side by side along *axis*
        (0 = X, 1 = Y, 2 = Z), separated by *spacing* units.

        Each object is centred on its own bounding-box midpoint so that
        they sit flush against each other with the requested gap.
        """
        if not self._objects:
            return

        cursor = 0.0
        for obj in self._objects:
            extent = obj.mesh.extents[axis] * obj.scale
            pos = np.zeros(3)
            pos[axis] = cursor + extent / 2.0
            obj.position = pos
            cursor += extent + spacing

        logger.info(
            "Auto-layout applied along axis %d to %d object(s).",
            axis,
            len(self._objects),
        )

    # ------------------------------------------------------------------
    # Compose / export
    # ------------------------------------------------------------------

    def compose(self) -> trimesh.Scene:
        """
        Build a trimesh.Scene from all registered objects.

        Each mesh is scaled and translated to its assigned position.
        Original mesh objects remain unmodified.
        """
        scene = trimesh.Scene()
        for obj in self._objects:
            mesh_copy = obj.mesh.copy()
            if obj.scale != 1.0:
                mesh_copy.apply_scale(obj.scale)
            transform = tf.translation_matrix(obj.position)
            mesh_copy.apply_transform(transform)
            scene.add_geometry(mesh_copy, geom_name=obj.name)

        logger.info("Scene composed with %d object(s).", len(self._objects))
        return scene

    def export(self, path: str) -> None:
        """Compose and export the scene to a GLB file at *path*."""
        scene = self.compose()
        scene.export(path)
        logger.info("Scene exported → %s", path)

    @property
    def object_count(self) -> int:
        return len(self._objects)
