"""
Mesh cleanup pipeline.

Removes degenerate and duplicate geometry, fills small holes,
fixes winding-order inconsistencies, and applies light smoothing —
all as discrete, logged steps.
"""
import logging

import trimesh
import trimesh.smoothing

from core.config import MeshConfig, config

logger = logging.getLogger(__name__)


class MeshCleaner:
    """
    Cleans raw generated meshes through a sequence of targeted operations.

    Each step is a private method so it can be individually overridden,
    skipped, or reordered in a subclass.

    Parameters
    ----------
    mesh_config:
        Overrides the global mesh config if supplied.
    """

    def __init__(self, mesh_config: MeshConfig | None = None) -> None:
        self.cfg = mesh_config or config.mesh

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clean(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Run the full cleanup pipeline on *mesh* and return the result.

        The pipeline (in order):
        1. Remove degenerate faces
        2. Rebuild — removes duplicates and unreferenced vertices
        3. Fill small holes  (if enabled)
        4. Fix normals        (if enabled)
        5. Laplacian smoothing (if iterations > 0)
        """
        logger.info("--- Mesh Cleanup Start ---")
        logger.info(
            "Input  — faces: %d, vertices: %d, watertight: %s",
            len(mesh.faces),
            len(mesh.vertices),
            mesh.is_watertight,
        )

        mesh = self._remove_degenerate_faces(mesh)
        mesh = self._rebuild(mesh)

        if self.cfg.hole_fill_enabled:
            mesh = self._fill_holes(mesh)

        if self.cfg.fix_normals:
            mesh = self._fix_normals(mesh)

        if self.cfg.smoothing_iterations > 0:
            mesh = self._smooth(mesh)

        logger.info(
            "Output — faces: %d, vertices: %d, watertight: %s",
            len(mesh.faces),
            len(mesh.vertices),
            mesh.is_watertight,
        )
        logger.info("--- Mesh Cleanup Complete ---")
        return mesh

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    def _remove_degenerate_faces(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        mask = mesh.nondegenerate_faces()
        removed = int((~mask).sum())
        if removed:
            logger.debug("Removed %d degenerate face(s).", removed)
        return trimesh.Trimesh(
            vertices=mesh.vertices,
            faces=mesh.faces[mask],
            process=False,
        )

    def _rebuild(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Re-process to strip duplicate faces and unreferenced vertices."""
        before = len(mesh.faces)
        mesh = trimesh.Trimesh(
            vertices=mesh.vertices,
            faces=mesh.faces,
            process=True,
        )
        removed = before - len(mesh.faces)
        if removed:
            logger.debug("Removed %d duplicate/redundant face(s).", removed)
        return mesh

    def _fill_holes(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        mesh.fill_holes()
        logger.debug("Hole filling applied.")
        return mesh

    def _fix_normals(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        mesh.fix_normals()
        logger.debug("Normals fixed.")
        return mesh

    def _smooth(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        trimesh.smoothing.filter_laplacian(
            mesh, iterations=self.cfg.smoothing_iterations
        )
        logger.debug(
            "Laplacian smoothing applied (%d iterations).",
            self.cfg.smoothing_iterations,
        )
        return mesh
