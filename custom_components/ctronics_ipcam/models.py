"""What each config entry keeps at runtime."""
from __future__ import annotations

from dataclasses import dataclass

from .const import DEFAULT_PTZ_SPEED
from .coordinator import CtronicsCoordinator


@dataclass
class CtronicsRuntime:
    """Everything the platforms need, stored per config entry."""

    coordinator: CtronicsCoordinator

    # The camera stores neither of these, and offers no command to read them
    # back — in its own web interface they are just two form fields. So they
    # live here, shared between the number entities that set them and the
    # buttons that act on them, and are restored across restarts by the
    # number entities themselves.
    ptz_speed: int = DEFAULT_PTZ_SPEED
    # 1-based, exactly as the camera's "Voreinstellung" field shows it.
    preset_slot: int = 1
