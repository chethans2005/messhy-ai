import torch
import trimesh
import numpy as np
from shap_e.diffusion.sample import sample_latents
from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
from shap_e.models.download import load_model, load_config
from shap_e.util.notebooks import decode_latent_mesh

from core.device import get_device


class ShapEGenerator:
    """
    Handles text-to-mesh generation using Shap-E.
    """

    def __init__(self):
        self.device = get_device()
        self.model = None      # text300M  — used for latent sampling
        self.xm = None         # transmitter — used for mesh decoding
        self.diffusion = None
        self._load_model()

    def _load_model(self):
        print("Loading Shap-E models...")
        self.model = load_model("text300M", device=self.device)
        self.xm = load_model("transmitter", device=self.device)
        self.diffusion = diffusion_from_config(load_config("diffusion"))
        print("Shap-E models loaded successfully.")

    def generate_mesh(self, prompt: str, guidance_scale: float = 15.0, karras_steps: int = 64):
        """
        Generates a mesh from a text prompt.
        Returns a trimesh object.
        """
        print(f"Generating mesh for prompt: {prompt}")

        latents = sample_latents(
            batch_size=1,
            model=self.model,
            diffusion=self.diffusion,
            guidance_scale=guidance_scale,
            model_kwargs=dict(texts=[prompt]),
            progress=True,
            clip_denoised=True,
            use_fp16=(self.device.type == "cuda"),
            use_karras=True,
            karras_steps=karras_steps,
            sigma_min=1e-3,
            sigma_max=160,
            s_churn=0,
        )

        tri = decode_latent_mesh(self.xm, latents[0]).tri_mesh()
        mesh = trimesh.Trimesh(
            vertices=np.array(tri.verts),
            faces=np.array(tri.faces),
            process=False,
        )
        return mesh