# Text → 3D Mesh Generator

A production-style Python backend that turns a text prompt into a clean, downloadable **GLB** file using [Shap-E](https://github.com/openai/shap-e) — with a minimal web UI served by Flask.

---

## Demo

1. Type a prompt: `"a wooden chair with four legs"`
2. Wait ~3 minutes (GPU generation)
3. Download the `.glb` file and open it in any 3D viewer

---

## Pipeline

```text
Text Prompt
  → Shap-E diffusion (64-step Karras sampler)
  → Raw GLB saved
  → Mesh cleanup  (degenerate faces, duplicates, hole fill, normals, smoothing)
  → Mesh validation  (watertight, winding, face count, NaN check)
  → Clean GLB saved
  → Metrics logged to JSONL
```

---

## Project structure

```
backend/
  api.py                   ← Flask web server (run this)
  main.py                  ← CLI entry point
  core/
    config.py              ← All tuneable parameters
    device.py              ← GPU/CPU detection
    utils.py               ← Logging, path helpers
  generation/
    router.py              ← Engine router (pluggable)
    shap_e_generator.py    ← Shap-E text-to-mesh
  mesh_processing/
    cleanup.py             ← Degenerate removal, smoothing, normals
    smoothing.py           ← Laplacian / Taubin / Humphrey
    validation.py          ← Watertight, winding, volume checks
  composition/
    scene_composer.py      ← Multi-mesh scene assembly
  evaluation/
    metrics.py             ← Timing + quality metrics
    logger.py              ← JSONL run logger
  outputs/
    raw/                   ← Raw generated GLBs
    cleaned/               ← Post-processed GLBs
    logs/                  ← generation_log.jsonl

frontend/
  index.html               ← Minimal web UI (served by Flask)
```

---

## Requirements

- Python 3.11+
- NVIDIA GPU with CUDA 12+ (tested on RTX 3050 6 GB)
- ~4 GB VRAM minimum

---

## Setup

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/mesh-project.git
cd mesh-project
```

### 2. Create virtual environment

```bash
python -m venv mesh-env
# Windows
mesh-env\Scripts\activate
# Linux / macOS
source mesh-env/bin/activate
```

### 3. Install PyTorch (CUDA build)

Choose the command matching your CUDA version from https://pytorch.org/get-started/locally/

```bash
# Example for CUDA 12.8
pip install torch --index-url https://download.pytorch.org/whl/cu128
```

### 4. Install remaining dependencies

```bash
pip install -r requirements.txt
```

---

## Running

### Web UI

```bash
cd backend
python api.py
```

Open **http://localhost:5000**, enter a prompt, and download the GLB when it's ready.

### CLI

```bash
cd backend
python main.py "a wooden table with two drawers"
```

Outputs saved to `backend/outputs/cleaned/`.

---

## Configuration

All parameters (diffusion steps, guidance scale, smoothing iterations, face count limits, output paths) are in [`backend/core/config.py`](backend/core/config.py). No magic numbers elsewhere.

---

## Tech stack

| Layer | Library |
|---|---|
| Diffusion model | [Shap-E](https://github.com/openai/shap-e) (OpenAI) |
| Deep learning | PyTorch 2.10 + CUDA 12.8 |
| Mesh processing | trimesh 4.11 |
| Web server | Flask 3.1 |
| Frontend | Vanilla HTML/CSS/JS |

---

## Notes

- Generation takes **2–4 minutes** on a mid-range laptop GPU
- The `pytorch3d` warning during generation is harmless — Shap-E falls back to its built-in renderer automatically
- Model weights are downloaded automatically by Shap-E on first run (~1 GB)

Issues, ideas, and feedback are welcome. If you open an issue, include your prompt, settings, and output artifacts to make reproduction easier.
