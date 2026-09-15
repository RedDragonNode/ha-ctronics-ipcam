"""Image entity showing the snapshot from the camera's last detection."""
from __future__ import annotations

from homeassistant.components.image import ImageEntity, ImageEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import build_device_info
from .models import CtronicsRuntime


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime: CtronicsRuntime = hass.data[DOMAIN][entry.entry_id]
    if runtime.watcher is None:
        return
    async_add_entities(
        [CtronicsLastDetectionImage(hass, runtime, entry, entry.data[CONF_HOST])]
    )


class CtronicsLastDetectionImage(ImageEntity):
    """Serves the most recent alarm snapshot, so it can go on a dashboard.

    The file itself lives in the folder the camera uploads to, which Home
    Assistant does not serve over HTTP — this entity reads it and hands it to
    the frontend, so no extra `local_file` camera is needed.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description = ImageEntityDescription(
        key="last_detection",
        translation_key="last_detection",
    )

    def __init__(
        self,
        hass: HomeAssistant,
        runtime: CtronicsRuntime,
        entry: ConfigEntry,
        host: str,
    ) -> None:
        super().__init__(hass)
        assert runtime.watcher is not None
        self._watcher = runtime.watcher
        self._attr_unique_id = f"{entry.entry_id}_last_detection"
        self._attr_device_info = build_device_info(entry, host)
        self._attr_image_last_updated = runtime.watcher.last_detected

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._watcher.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        if self._watcher.last_detected != self._attr_image_last_updated:
            self._attr_image_last_updated = self._watcher.last_detected
            # Tell the frontend the cached picture is stale.
            self._cached_image = None
        self.async_write_ha_state()

    async def async_image(self) -> bytes | None:
        return await self._watcher.async_image_bytes()
