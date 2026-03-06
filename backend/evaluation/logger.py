"""
System logger — persists generation run records as structured JSONL.

Each call to log_run() appends one JSON object per line to
outputs/logs/generation_log.jsonl, making it easy to parse with
pandas, jq, or any line-oriented JSON tool.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from evaluation.metrics import GenerationMetrics

logger = logging.getLogger(__name__)


class SystemLogger:
    """
    Persists generation metrics as newline-delimited JSON (JSONL).

    Parameters
    ----------
    log_dir:
        Directory where ``generation_log.jsonl`` is written.
        Created automatically if it does not exist.
    """

    _LOG_FILENAME = "generation_log.jsonl"

    def __init__(self, log_dir: "str | Path" = "outputs/logs") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self.log_dir / self._LOG_FILENAME
        logger.info("SystemLogger → %s", self._log_file)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_run(
        self,
        metrics: GenerationMetrics,
        output_path: Optional[str] = None,
    ) -> None:
        """
        Append one record to the JSONL log file.

        Parameters
        ----------
        metrics:
            Finalized GenerationMetrics from a pipeline run.
        output_path:
            Absolute or relative path of the exported GLB file, if any.
        """
        record = self._build_record(metrics, output_path)
        with self._log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("Run record appended → %s", self._log_file)

    def read_all(self) -> list[dict]:
        """
        Return all records from the log file as a list of dicts.
        Returns an empty list if the file does not yet exist.
        """
        if not self._log_file.exists():
            return []
        records: list[dict] = []
        with self._log_file.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_record(
        m: GenerationMetrics, output_path: Optional[str]
    ) -> dict:
        return {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "prompt": m.prompt,
            "engine": m.engine,
            "generation_time_s": round(m.generation_time_s, 3),
            "cleanup_time_s": round(m.cleanup_time_s, 3),
            "total_time_s": round(m.total_time_s, 3),
            "raw_faces": m.raw_face_count,
            "raw_vertices": m.raw_vertex_count,
            "clean_faces": m.clean_face_count,
            "clean_vertices": m.clean_vertex_count,
            "is_valid": m.validation.is_valid if m.validation else None,
            "is_watertight": (
                m.validation.is_watertight if m.validation else None
            ),
            "is_winding_consistent": (
                m.validation.is_winding_consistent if m.validation else None
            ),
            "surface_area": (
                round(m.validation.surface_area, 4) if m.validation else None
            ),
            "volume": (
                round(m.validation.volume, 4)
                if m.validation and m.validation.volume is not None
                else None
            ),
            "output_path": output_path,
        }
