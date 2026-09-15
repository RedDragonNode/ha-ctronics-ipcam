"""Data update coordinator for the Ctronics IP Camera integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CtronicsApiError, CtronicsClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CtronicsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the camera's current AI-detection / Auto-Tracking / IR state."""

    def __init__(self, hass: HomeAssistant, client: CtronicsClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            smd_enabled = await self.client.get_smd_enabled()
            smd_ex = await self.client.get_smd_ex()
            smartrack_enabled = await self.client.get_smartrack_enabled()
        except CtronicsApiError as err:
            # These three are the commands we know exist, so a failure here is
            # a real connection/auth problem worth surfacing.
            raise UpdateFailed(f"Error talking to camera: {err}") from err

        # These two degrade gracefully instead of taking the whole update down.
        infrared_mode = await self.client.get_infrared_mode()
        ircut_value = await self.client.get_ircut_switch_value()

        return {
            "smd_enabled": smd_enabled,
            "smd_gthresh": int(smd_ex.get("smd_gthresh", 50) or 50),
            "smd_rect": smd_ex.get("smd_rect", "0"),
            "smd_type": smd_ex.get("smd_type", "0"),
            "smartrack_enabled": smartrack_enabled,
            "infrared_mode": infrared_mode,
            "ircut_value": ircut_value,
        }
