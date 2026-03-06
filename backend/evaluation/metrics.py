"""
Generation metrics — collects timing and quality data across the pipeline.

MetricsCollector is a lightweight accumulator that pipeline stages write
to as they complete.  Call finalize() at the end to get the full report.
"""
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import trimesh

if TYPE_CHECKING:
    from mesh_processing.validation import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class GenerationMetrics:
    """All measurements from a single text-to-mesh pipeline run."""

    prompt: str
    engine: str
    generation_time_s: float = 0.0
    cleanup_time_s: float = 0.0
    total_time_s: float = 0.0
    raw_face_count: int = 0
    raw_vertex_count: int = 0
    clean_face_count: int = 0
    clean_vertex_count: int = 0
    validation: Optional["ValidationResult"] = None

    def log_report(self) -> None:
        """Emit a structured summary to the logger."""
        logger.info("=== Generation Metrics ===")
        logger.info("  Prompt:           '%s'", self.prompt)
        logger.info("  Engine:           %s", self.engine)
        logger.info("  Generation time:  %.2f s", self.generation_time_s)
        logger.info("  Cleanup time:     %.2f s", self.cleanup_time_s)
        logger.info("  Total time:       %.2f s", self.total_time_s)
        logger.info(
            "  Raw mesh:         %d faces, %d vertices",
            self.raw_face_count,
            self.raw_vertex_count,
        )
        logger.info(
            "  Clean mesh:       %d faces, %d vertices",
            self.clean_face_count,
            self.clean_vertex_count,
        )
        if self.validation is not None:
            logger.info(
                "  Valid:            %s  |  Watertight: %s",
                self.validation.is_valid,
                self.validation.is_watertight,
            )


class MetricsCollector:
    """
    Accumulates timing and quality metrics for a single pipeline run.

    Usage
    -----
    >>> collector = MetricsCollector(prompt="a red chair", engine="shap_e")
    >>> collector.start_pipeline()
    >>> # ... generate ...
    >>> collector.record_generation(elapsed, raw_mesh)
    >>> # ... clean ...
    >>> collector.record_cleanup(elapsed, clean_mesh)
    >>> collector.record_validation(validation_result)
    >>> metrics = collector.finalize()
    """

    def __init__(self, prompt: str, engine: str = "shap_e") -> None:
        self._metrics = GenerationMetrics(prompt=prompt, engine=engine)
        self._pipeline_start: float = 0.0

    def start_pipeline(self) -> None:
        """Mark the start of the pipeline wall-clock timer."""
        self._pipeline_start = time.perf_counter()

    def record_generation(
        self, elapsed: float, mesh: trimesh.Trimesh
    ) -> None:
        """Record generation timing and raw mesh stats."""
        self._metrics.generation_time_s = elapsed
        self._metrics.raw_face_count = len(mesh.faces)
        self._metrics.raw_vertex_count = len(mesh.vertices)

    def record_cleanup(
        self, elapsed: float, mesh: trimesh.Trimesh
    ) -> None:
        """Record cleanup timing and clean mesh stats."""
        self._metrics.cleanup_time_s = elapsed
        self._metrics.clean_face_count = len(mesh.faces)
        self._metrics.clean_vertex_count = len(mesh.vertices)

    def record_validation(self, result: "ValidationResult") -> None:
        """Attach a ValidationResult to the metrics."""
        self._metrics.validation = result

    def finalize(self) -> GenerationMetrics:
        """
        Compute total elapsed time, log the report, and return the metrics.
        """
        self._metrics.total_time_s = (
            time.perf_counter() - self._pipeline_start
        )
        self._metrics.log_report()
        return self._metrics
