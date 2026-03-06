"""
Mesh validation — structural and geometric quality checks.

Produces a structured ValidationResult dataclass so downstream code
(metrics, logger) can consume the results without parsing log strings.
"""
import logging
from dataclasses import dataclass, field

import numpy as np
import trimesh

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Structured output of a single mesh validation run."""

    is_valid: bool
    is_watertight: bool
    is_winding_consistent: bool
    face_count: int
    vertex_count: int
    bounding_box: tuple[float, float, float]   # (width, height, depth)
    surface_area: float
    volume: float | None                        # None when not a closed volume
    issues: list[str] = field(default_factory=list)

    def log_summary(self) -> None:
        status = "PASSED" if self.is_valid else "FAILED"
        logger.info("=== Mesh Validation %s ===", status)
        logger.info("  Watertight:         %s", self.is_watertight)
        logger.info("  Winding consistent: %s", self.is_winding_consistent)
        logger.info("  Faces:              %d", self.face_count)
        logger.info("  Vertices:           %d", self.vertex_count)
        logger.info(
            "  Bounding box:       %.4f x %.4f x %.4f", *self.bounding_box
        )
        logger.info("  Surface area:       %.4f", self.surface_area)
        if self.volume is not None:
            logger.info("  Volume:             %.4f", self.volume)
        for issue in self.issues:
            logger.warning("  [Issue] %s", issue)


class MeshValidator:
    """
    Validates mesh quality across several dimensions:

    - Geometric integrity (NaN vertices, trimesh validity flag)
    - Watertightness (closed surface, no boundary edges)
    - Face count within acceptable bounds
    - Volume / surface area (computed when watertight)

    Parameters
    ----------
    min_faces:
        Minimum acceptable face count.
    max_faces:
        Maximum acceptable face count.
    """

    def __init__(self, min_faces: int = 100, max_faces: int = 500_000) -> None:
        self.min_faces = min_faces
        self.max_faces = max_faces

    def validate(self, mesh: trimesh.Trimesh) -> ValidationResult:
        """
        Run all checks and return a :class:`ValidationResult`.

        Never raises — all detected problems are recorded as *issues*.
        """
        logger.info("Running mesh validation ...")
        issues: list[str] = []

        is_watertight = bool(mesh.is_watertight)
        # is_winding_consistent: all face normals point coherently outward
        # is_empty: mesh has no faces at all
        is_winding_consistent = bool(mesh.is_winding_consistent)
        face_count = len(mesh.faces)
        vertex_count = len(mesh.vertices)
        bounding_box: tuple[float, float, float] = tuple(
            float(x) for x in mesh.extents.tolist()
        )  # type: ignore[assignment]
        surface_area = float(mesh.area)
        # Volume is only meaningful (and non-zero) for closed, consistently
        # wound meshes — guard with is_watertight AND is_winding_consistent.
        volume: float | None = (
            float(mesh.volume)
            if (is_watertight and is_winding_consistent)
            else None
        )

        # --- checks ---
        if not is_watertight:
            issues.append("Mesh is not watertight (open boundary edges detected).")

        if face_count < self.min_faces:
            issues.append(
                f"Face count ({face_count}) is below minimum ({self.min_faces})."
            )
        if face_count > self.max_faces:
            issues.append(
                f"Face count ({face_count}) exceeds maximum ({self.max_faces})."
            )

        if not is_winding_consistent:
            issues.append("Winding order is inconsistent (normals may be inverted on some faces).")

        if mesh.is_empty:
            issues.append("Mesh is empty (no faces).")

        if np.any(np.isnan(mesh.vertices)):
            issues.append("NaN values detected in vertex positions.")

        if surface_area <= 0:
            issues.append("Surface area is zero or negative.")

        is_valid = len(issues) == 0
        result = ValidationResult(
            is_valid=is_valid,
            is_watertight=is_watertight,
            is_winding_consistent=is_winding_consistent,
            face_count=face_count,
            vertex_count=vertex_count,
            bounding_box=bounding_box,
            surface_area=surface_area,
            volume=volume,
            issues=issues,
        )
        result.log_summary()
        return result
