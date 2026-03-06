"""
Entry point for the text-to-3D mesh generation backend.

Pipeline
--------
Text prompt
  → GenerationRouter  (Shap-E by default)
  → MeshCleaner
  → MeshValidator
  → Export cleaned GLB
  → MetricsCollector / SystemLogger
"""
import logging
import sys
import time

from core.config import config
from core.device import DeviceManager
from core.utils import ensure_dir, sanitize_filename, setup_logging
from evaluation.logger import SystemLogger
from evaluation.metrics import MetricsCollector
from generation.router import GenerationRouter
from mesh_processing.cleanup import MeshCleaner
from mesh_processing.validation import MeshValidator

logger = logging.getLogger(__name__)


def run_pipeline(prompt: str) -> str:
    """
    Execute the full text-to-mesh pipeline for *prompt*.

    Steps
    -----
    1. Generate raw mesh via GenerationRouter
    2. Save raw GLB to outputs/raw/
    3. Clean mesh via MeshCleaner
    4. Validate cleaned mesh via MeshValidator
    5. Save cleaned GLB to outputs/cleaned/
    6. Finalize and persist metrics
    """
    logger.info("=== Mesh Generation Pipeline — START ===")
    logger.info("Prompt: '%s'", prompt)

    # --- Paths -----------------------------------------------------------
    ensure_dir(config.paths.raw_dir)
    ensure_dir(config.paths.cleaned_dir)
    safe_name = sanitize_filename(prompt)
    raw_path = config.paths.raw_dir / f"{safe_name}_raw.glb"
    clean_path = config.paths.cleaned_dir / f"{safe_name}_clean.glb"

    # --- Metrics ---------------------------------------------------------
    collector = MetricsCollector(prompt=prompt, engine=config.engine)
    sys_logger = SystemLogger(log_dir=config.paths.outputs_dir / "logs")
    collector.start_pipeline()

    # --- Generation ------------------------------------------------------
    router = GenerationRouter(engine=config.engine)
    t0 = time.perf_counter()
    raw_mesh = router.generate(prompt)
    gen_elapsed = time.perf_counter() - t0
    collector.record_generation(elapsed=gen_elapsed, mesh=raw_mesh)

    raw_mesh.export(str(raw_path))
    logger.info("Raw mesh saved → %s", raw_path)

    # --- Cleanup ---------------------------------------------------------
    cleaner = MeshCleaner()
    t0 = time.perf_counter()
    clean_mesh = cleaner.clean(raw_mesh)
    cleanup_elapsed = time.perf_counter() - t0
    collector.record_cleanup(elapsed=cleanup_elapsed, mesh=clean_mesh)

    # --- Validation ------------------------------------------------------
    validator = MeshValidator(
        min_faces=config.mesh.min_faces,
        max_faces=config.mesh.max_faces,
    )
    validation_result = validator.validate(clean_mesh)
    collector.record_validation(validation_result)

    # --- Export ----------------------------------------------------------
    clean_mesh.export(str(clean_path))
    logger.info("Clean mesh saved → %s", clean_path)

    # --- Finalise --------------------------------------------------------
    final_metrics = collector.finalize()
    sys_logger.log_run(final_metrics, output_path=str(clean_path))

    logger.info("=== Mesh Generation Pipeline — COMPLETE ===")
    return str(clean_path)


def main() -> None:
    setup_logging(config.log_level)

    dm = DeviceManager()
    dm.log_info()

    if len(sys.argv) < 2:
        print('Usage: python main.py "your prompt here"')
        sys.exit(1)

    prompt = sys.argv[1].strip()
    if not prompt:
        print("Error: prompt cannot be empty.")
        sys.exit(1)

    run_pipeline(prompt)


if __name__ == "__main__":
    main()
