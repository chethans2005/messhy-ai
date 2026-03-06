"""
Text-to-mesh generator backed by the Shap-E diffusion model.

Loads text300M (text encoder + diffusion) and transmitter (mesh decoder)
on construction and exposes a single generate() entry point.
"""
import logging

import numpy as np
import trimesh
from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
from shap_e.diffusion.sample import sample_latents
from shap_e.models.download import load_config, load_model
from shap_e.util.notebooks import decode_latent_mesh

from core.config import GenerationConfig, config
from core.device import get_device

logger = logging.getLogger(__name__)


class ShapEGenerator:
    """
    Text-to-mesh generator using the Shap-E diffusion model.

    Loads two pre-trained models at construction time:
      - text300M  : encodes the text prompt and drives latent diffusion.
      - transmitter: decodes a latent vector into a triangle mesh.

    Parameters
    ----------
    gen_config:
        Overrides the global generation config if supplied.
    """

    def __init__(self, gen_config: GenerationConfig | None = None) -> None:
        self.device = get_device()
        self.gen_config = gen_config or config.generation
        self._model = None
        self._xm = None
        self._diffusion = None
        self._load_models()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _load_models(self) -> None:
        logger.info("Loading Shap-E models onto %s ...", self.device)
        self._model = load_model("text300M", device=self.device)
        self._xm = load_model("transmitter", device=self.device)
        self._diffusion = diffusion_from_config(load_config("diffusion"))
        logger.info("Shap-E models loaded successfully.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> trimesh.Trimesh:
        """
        Generate a raw triangle mesh from a text prompt.

        Parameters
        ----------
        prompt:
            Natural-language description of the 3D object to generate.

        Returns
        -------
        trimesh.Trimesh
            Raw (unprocessed) mesh decoded from the diffusion latent.
        """
        cfg = self.gen_config
        logger.info("Sampling latents for prompt: '%s'", prompt)
        logger.info(
            "Diffusion params — guidance_scale=%.1f, karras_steps=%d, "
            "sigma=[%.0e, %.0f]",
            cfg.guidance_scale,
            cfg.karras_steps,
            cfg.sigma_min,
            cfg.sigma_max,
        )

        latents = sample_latents(
            batch_size=1,
            model=self._model,
            diffusion=self._diffusion,
            guidance_scale=cfg.guidance_scale,
            model_kwargs={"texts": [prompt]},
            progress=True,
            clip_denoised=cfg.clip_denoised,
            use_fp16=(self.device.type == "cuda"),
            use_karras=cfg.use_karras,
            karras_steps=cfg.karras_steps,
            sigma_min=cfg.sigma_min,
            sigma_max=cfg.sigma_max,
            s_churn=cfg.s_churn,
            device=self.device,
        )

        logger.info("Decoding latent to triangle mesh ...")
        tri = decode_latent_mesh(self._xm, latents[0]).tri_mesh()
        mesh = trimesh.Trimesh(
            vertices=np.array(tri.verts),
            faces=np.array(tri.faces),
            process=False,
        )
        logger.info(
            "Raw mesh — %d vertices, %d faces",
            len(mesh.vertices),
            len(mesh.faces),
        )
        return mesh
