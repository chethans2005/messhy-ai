import logging

import torch

logger = logging.getLogger(__name__)

_manager: "DeviceManager | None" = None


class DeviceManager:
    """
    Manages device selection for GPU-aware workloads.
    Detects CUDA availability at construction time and exposes device info.
    """

    def __init__(self) -> None:
        if torch.cuda.is_available():
            self._device = torch.device("cuda")
        else:
            self._device = torch.device("cpu")
            logger.warning("CUDA not available — falling back to CPU.")

    @property
    def device(self) -> torch.device:
        return self._device

    def get_device(self) -> torch.device:
        return self._device

    def log_info(self) -> None:
        """Log active device and hardware details."""
        logger.info("Active device: %s", self._device)
        if self._device.type == "cuda":
            props = torch.cuda.get_device_properties(0)
            logger.info("  GPU:          %s", props.name)
            logger.info("  VRAM:         %.2f GB", props.total_memory / 1e9)
            logger.info("  CUDA version: %s", torch.version.cuda)
            logger.info(
                "  Compute cap:  %d.%d",
                props.major,
                props.minor,
            )


def get_device() -> torch.device:
    """Module-level convenience wrapper — returns the active torch.device."""
    global _manager
    if _manager is None:
        _manager = DeviceManager()
    return _manager.get_device()


# Kept for backward compatibility with existing callers.
def print_device_info() -> None:
    DeviceManager().log_info()
