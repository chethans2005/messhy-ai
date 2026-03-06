"""
Standalone smoothing operations for fine-grained surface quality control.

Use these after MeshCleaner when you need to apply a specific algorithm
rather than the default Laplacian pass bundled in the cleanup pipeline.
"""
import logging

import trimesh
import trimesh.smoothing

logger = logging.getLogger(__name__)


class MeshSmoother:
    """
    Collection of mesh smoothing algorithms wrapping trimesh's built-ins.

    All methods operate in-place on the mesh and return it for chaining.
    """

    def laplacian(
        self, mesh: trimesh.Trimesh, iterations: int = 5
    ) -> trimesh.Trimesh:
        """
        Laplacian smoothing.

        Moves each vertex toward the average position of its neighbours.
        Fast and effective for reducing high-frequency noise, but can cause
        mesh shrinkage over many iterations.
        """
        logger.info(
            "Applying Laplacian smoothing (%d iterations) ...", iterations
        )
        trimesh.smoothing.filter_laplacian(mesh, iterations=iterations)
        logger.debug(
            "Post-Laplacian — faces: %d, vertices: %d",
            len(mesh.faces),
            len(mesh.vertices),
        )
        return mesh

    def taubin(
        self, mesh: trimesh.Trimesh, iterations: int = 10
    ) -> trimesh.Trimesh:
        """
        Taubin smoothing (volume-preserving).

        Alternates positive and negative Laplacian passes to counteract
        shrinkage.  Preferred over plain Laplacian for organic shapes.
        """
        logger.info("Applying Taubin smoothing (%d iterations) ...", iterations)
        trimesh.smoothing.filter_taubin(mesh, iterations=iterations)
        logger.debug(
            "Post-Taubin — faces: %d, vertices: %d",
            len(mesh.faces),
            len(mesh.vertices),
        )
        return mesh

    def humphrey(
        self, mesh: trimesh.Trimesh, iterations: int = 5
    ) -> trimesh.Trimesh:
        """
        Humphrey smoothing (feature-preserving).

        Better preserves sharp edges and corners compared to plain Laplacian.
        """
        logger.info(
            "Applying Humphrey smoothing (%d iterations) ...", iterations
        )
        trimesh.smoothing.filter_humphrey(mesh, iterations=iterations)
        logger.debug(
            "Post-Humphrey — faces: %d, vertices: %d",
            len(mesh.faces),
            len(mesh.vertices),
        )
        return mesh
