"""Camera entity serving the camera's own still-image endpoint.

This is deliberately NOT a second copy of the ONVIF/RTSP live stream — Home
Assistant's built-in ONVIF integration already provides that. What it adds is
a still image pulled straight from the camera (``/tmpfs/auto.jpg``), which:

  * works without a stream running at all, so it costs the camera far less,
  * is the full 3840x2160 sensor image,
  * and can be used by every Home Assistant feature that expects a camera
    entity (dashboard picture cards, notifications with an image, the
    built-in ``camera.snapshot`` service, ...).
"""
from __future__ import annotations

import logging

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CtronicsApiError
from .const import DOMAIN, SNAPSHOT_FRAME_INTERVAL
from .coordinator import CtronicsCoordinator
from .entity import build_device_info
from .models import CtronicsRuntime

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime: CtronicsRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [CtronicsSnapshotCamera(runtime.coordinator, entry, entry.data[CONF_HOST])]
    )


class CtronicsSnapshotCamera(Camera):
    """Still image from the camera, refreshed on demand."""

    _attr_has_entity_name = True
    _attr_translation_key = "snapshot"

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__()
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_snapshot"
        self._attr_device_info = build_device_info(entry, host)
        # Home Assistant asks for a new image at most this often. The camera
        # is a small embedded device and auto.jpg doesn't refresh faster than
        # this anyway, so polling harder would only cost it CPU.
        self._attr_frame_interval = SNAPSHOT_FRAME_INTERVAL

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the current still image, or None so HA keeps the last one."""
        try:
            return await self.coordinator.client.get_snapshot()
        except CtronicsApiError as err:
            _LOGGER.debug("Snapshot unavailable: %s", err)
            return None
