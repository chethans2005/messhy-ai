"""
Generation router — decouples the pipeline from any specific engine.

New generation backends can be plugged in at runtime via register_engine()
without modifying the pipeline code.
"""
import logging
from typing import Protocol, runtime_checkable

import trimesh

logger = logging.getLogger(__name__)


@runtime_checkable
class MeshGeneratorProtocol(Protocol):
    """Any object that can produce a trimesh.Trimesh from a text prompt."""

    def generate(self, prompt: str) -> trimesh.Trimesh:
        ...


class GenerationRouter:
    """
    Routes generation requests to a registered engine.

    Parameters
    ----------
    engine:
        Name of the engine to use by default. Must be one of
        ``SUPPORTED_ENGINES`` or registered via register_engine().
    """

    SUPPORTED_ENGINES: frozenset[str] = frozenset({"shap_e"})

    def __init__(self, engine: str = "shap_e") -> None:
        self._default_engine = engine
        self._engines: dict[str, MeshGeneratorProtocol] = {}
        self._init_engine(engine)

    # ------------------------------------------------------------------
    # Engine management
    # ------------------------------------------------------------------

    def _init_engine(self, engine: str) -> None:
        if engine not in self.SUPPORTED_ENGINES:
            raise ValueError(
                f"Unknown engine '{engine}'. "
                f"Supported built-in engines: {sorted(self.SUPPORTED_ENGINES)}"
            )
        if engine == "shap_e":
            # Lazy import keeps startup time fast when the router is
            # instantiated but a different engine is later registered.
            from generation.shap_e_generator import ShapEGenerator

            self._engines["shap_e"] = ShapEGenerator()

        logger.info("Generation router ready — default engine: %s", engine)

    def register_engine(self, name: str, engine: MeshGeneratorProtocol) -> None:
        """
        Register a custom generation engine at runtime.

        Parameters
        ----------
        name:
            Unique identifier for the engine.
        engine:
            Any object satisfying :class:`MeshGeneratorProtocol`.
        """
        if not isinstance(engine, MeshGeneratorProtocol):
            raise TypeError(
                f"'{name}' does not satisfy MeshGeneratorProtocol "
                f"(must implement generate(prompt: str) -> trimesh.Trimesh)."
            )
        self._engines[name] = engine
        logger.info("Registered generation engine: '%s'", name)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def generate(self, prompt: str, engine: str | None = None) -> trimesh.Trimesh:
        """
        Generate a mesh from a text prompt.

        Parameters
        ----------
        prompt:
            Natural-language description of the 3D object.
        engine:
            Engine override.  Uses the router's default when omitted.

        Returns
        -------
        trimesh.Trimesh
            Raw mesh returned by the chosen engine.
        """
        target = engine or self._default_engine
        if target not in self._engines:
            raise ValueError(
                f"Engine '{target}' is not registered. "
                f"Available: {list(self._engines)}"
            )
        logger.info("Routing request to engine '%s': '%s'", target, prompt)
        return self._engines[target].generate(prompt)
