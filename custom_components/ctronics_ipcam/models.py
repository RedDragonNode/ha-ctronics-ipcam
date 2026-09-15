"""What each config entry keeps at runtime."""
from __future__ import annotations

from dataclasses import dataclass

from .coordinator import CtronicsCoordinator


@dataclass
class CtronicsRuntime:
    """Everything the platforms need, stored per config entry."""

    coordinator: CtronicsCoordinator
