"""What each config entry keeps at runtime."""
from __future__ import annotations

from dataclasses import dataclass

from .alarm_watcher import AlarmFolderWatcher
from .coordinator import CtronicsCoordinator


@dataclass
class CtronicsRuntime:
    """Everything the platforms need, stored per config entry."""

    coordinator: CtronicsCoordinator
    # None when no alarm folder is configured — then there is no person
    # detection and the binary_sensor / image entities are not created.
    watcher: AlarmFolderWatcher | None = None
