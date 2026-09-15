"""Camera entities: the two RTSP streams and a still-image snapshot.

Home Assistant's built-in ONVIF integration also exposes the two streams. The
point of having them here is that everything about the camera then sits on a
single device — streams, snapshot, PTZ presets and the camera's own settings
— instead of being split across two.

All three entities share one still image: the camera's own snapshot endpoint.
That is a full 3840x2160 frame fetched over plain HTTP, which is both sharper
and far cheaper than decoding a keyframe out of RTSP.
"""
from __future__ import annotations

import logging

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CtronicsApiError
from .const import (
    CONF_RTSP_MAIN_PATH,
    CONF_RTSP_PORT,
    CONF_RTSP_SUB_PATH,
    DEFAULT_RTSP_MAIN_PATH,
    DEFAULT_RTSP_PORT,
    DEFAULT_RTSP_SUB_PATH,
    DOMAIN,
    SNAPSHOT_FRAME_INTERVAL,
)
from .coordinator import CtronicsCoordinator
from .entity import build_device_info
from .models import CtronicsRuntime

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime: CtronicsRuntime = hass.data[DOMAIN][entry.entry_id]
    coordinator = runtime.coordinator
    host = entry.data[CONF_HOST]
    options = entry.options

    rtsp_port = options.get(CONF_RTSP_PORT, DEFAULT_RTSP_PORT)
    main_path = (
        options.get(CONF_RTSP_MAIN_PATH) or DEFAULT_RTSP_MAIN_PATH
    ).strip()
    sub_path = (options.get(CONF_RTSP_SUB_PATH) or DEFAULT_RTSP_SUB_PATH).strip()

    async_add_entities(
        [
            CtronicsSnapshotCamera(coordinator, entry, host),
            CtronicsStreamCamera(
                coordinator, entry, host, "main_stream", main_path, rtsp_port
            ),
            CtronicsStreamCamera(
                coordinator, entry, host, "sub_stream", sub_path, rtsp_port
            ),
        ]
    )


class CtronicsBaseCamera(Camera):
    """Shared still-image handling for every camera entity here."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__()
        self.coordinator = coordinator
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


class CtronicsSnapshotCamera(CtronicsBaseCamera):
    """Still image only — no stream, so it costs the camera almost nothing."""

    _attr_translation_key = "snapshot"

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__(coordinator, entry, host)
        self._attr_unique_id = f"{entry.entry_id}_snapshot"


class CtronicsStreamCamera(CtronicsBaseCamera):
    """One of the camera's two RTSP streams, with the HTTP still as preview."""

    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(
        self,
        coordinator: CtronicsCoordinator,
        entry: ConfigEntry,
        host: str,
        key: str,
        path: str,
        port: int,
    ) -> None:
        super().__init__(coordinator, entry, host)
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._path = path
        self._port = port

    async def stream_source(self) -> str | None:
        """The RTSP URL Home Assistant's stream component connects to.

        Built fresh each time rather than cached, so a changed password or
        stream path takes effect on the next reload.
        """
        return self.coordinator.client.rtsp_url(self._path, self._port)
