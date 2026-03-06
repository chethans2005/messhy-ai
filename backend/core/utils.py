"""
Shared utility helpers used across the backend.
"""
import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with a consistent timestamp format."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )


def ensure_dir(path: "Path | str") -> Path:
    """Create *path* (and any parents) if it does not already exist."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(name: str, max_length: int = 64) -> str:
    """
    Convert an arbitrary string into a safe filesystem filename.
    Keeps alphanumerics, spaces, underscores, and hyphens; replaces everything
    else with underscores; collapses whitespace to underscores.
    """
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
    return safe.strip().replace(" ", "_")[:max_length]


@contextmanager
def timer(label: str = "Operation") -> Generator[None, None, None]:
    """Context manager that logs the wall-clock duration of a block."""
    logger = logging.getLogger(__name__)
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("%s completed in %.2f s", label, elapsed)
