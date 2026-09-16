"""What each config entry keeps at runtime."""
from __future__ import annotations

from dataclasses import dataclass

from .coordinator import CtronicsCoordinator


@dataclass
class CtronicsRuntime:
    """Everything the platforms need, stored per config entry."""

    coordinator: CtronicsCoordinator

    # The camera offers no command to read this back — in its own web
    # interface it is just a form field. So it lives here, shared between the
    # number entity that sets it and the buttons that act on it, and is
    # restored across restarts by the number entity itself.
    # 1-based, exactly as the camera's "Voreinstellung" field shows it.
    preset_slot: int = 1
