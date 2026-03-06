"""
Global configuration for the mesh generation backend.
All tuneable parameters live here — no magic numbers scattered across modules.
"""
from dataclasses import dataclass, field
from pathlib import Path

# Root of the backend/ directory (two levels up from this file at core/config.py)
_BACKEND_DIR = Path(__file__).resolve().parent.parent


@dataclass
class GenerationConfig:
    """Diffusion-sampling parameters forwarded to Shap-E."""

    guidance_scale: float = 15.0
    karras_steps: int = 64
    sigma_min: float = 1e-3
    sigma_max: float = 160.0
    s_churn: float = 0.0
    use_karras: bool = True
    clip_denoised: bool = True


@dataclass
class MeshConfig:
    """Quality gates and processing toggles for the mesh pipeline."""

    smoothing_iterations: int = 5
    hole_fill_enabled: bool = True
    fix_normals: bool = True
    min_faces: int = 100
    max_faces: int = 500_000


@dataclass
class PathConfig:
    """All filesystem paths used by the backend."""

    outputs_dir: Path = field(default_factory=lambda: _BACKEND_DIR / "outputs")
    raw_dir: Path = field(default_factory=lambda: _BACKEND_DIR / "outputs" / "raw")
    cleaned_dir: Path = field(
        default_factory=lambda: _BACKEND_DIR / "outputs" / "cleaned"
    )
    model_cache_dir: Path = field(
        default_factory=lambda: _BACKEND_DIR / "shap_e_model_cache"
    )


@dataclass
class AppConfig:
    """Top-level config aggregating all sub-configs."""

    generation: GenerationConfig = field(default_factory=GenerationConfig)
    mesh: MeshConfig = field(default_factory=MeshConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    log_level: str = "INFO"
    engine: str = "shap_e"


# Module-level singleton — import and use directly.
config = AppConfig()
