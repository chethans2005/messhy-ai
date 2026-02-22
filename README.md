# Hybrid Multi-Object Text & Image to 3D Mesh Generation

Generate clean, composition-ready 3D meshes from text prompts and reference images using a hybrid pipeline that prioritizes **controllability** and **mesh usability**.

## What this project does

- Converts text and/or images into per-object 3D meshes
- Refines generated meshes for topology quality and downstream use
- Composes multiple objects into a coherent scene with deterministic placement rules
- Provides a web-based 3D preview and mesh export workflow

## Why this approach

End-to-end scene generation is often hard to control. This project focuses on object-level generation plus deterministic composition so outputs are easier to validate, edit, and reuse in real 3D pipelines (Blender, Unity, Unreal Engine).

## Pipeline

```text
Text Prompt or Input Image
	↓
Prompt Decomposition
	↓
Text→3D  or  Text→Image→3D  or  Image→3D
	↓
Per-Object Mesh Cleanup + Scale Normalization
	↓
Scene Composition Engine (placement + collision checks)
	↓
Validation + Metrics
	↓
Web Viewer + Export (GLB/OBJ)
```

## Core features

### Hybrid generation modes
- Text → Mesh
- Text → Image → Mesh
- Image → Mesh

### Mesh refinement
- Non-manifold edge correction
- Normal recalculation
- Triangle count optimization
- Scale normalization

### Multi-object composition
- Prompt decomposition into objects and relations
- Deterministic placement with relative spatial rules
- Bounding-box collision avoidance

### Evaluation and preview
- Mesh validity checks
- Triangle count and generation-time logging
- Interactive Three.js viewer (orbit, wireframe, toggle, export)

## Tech stack

- **Backend:** Python, PyTorch, Trimesh/Open3D
- **Frontend:** React, Three.js
- **Compute target:** Single-GPU friendly development setup

## Current status

This repository is an active research/prototyping effort focused on practical text/image-to-3D workflows. APIs, modules, and folder layout may evolve as experiments continue.

## Limitations

- Spatial reasoning is currently rule-based
- Physics-aware realism is not included
- Results depend on the strengths/limits of upstream pretrained generators

## Roadmap

- Learned spatial reasoning for scene layout
- Physics-aware composition constraints
- Improved texture/material quality
- Broader prompt robustness benchmarking

## Contributing

Issues, ideas, and feedback are welcome. If you open an issue, include your prompt, settings, and output artifacts to make reproduction easier.
