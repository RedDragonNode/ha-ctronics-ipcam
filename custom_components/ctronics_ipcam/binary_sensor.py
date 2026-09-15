"""Binary sensor: the camera's AI person detection, via its alarm snapshots."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import build_device_info
from .models import CtronicsRuntime


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime: CtronicsRuntime = hass.data[DOMAIN][entry.entry_id]
    if runtime.watcher is None:
        # No alarm folder configured — nothing to detect with.
        return
    async_add_entities(
        [CtronicsPersonDetectedSensor(runtime, entry, entry.data[CONF_HOST])]
    )


class CtronicsPersonDetectedSensor(BinarySensorEntity):
    """On while the camera keeps reporting a person, off after the quiet period."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description = BinarySensorEntityDescription(
        key="person_detected",
        translation_key="person_detected",
        device_class=BinarySensorDeviceClass.MOTION,
    )

    def __init__(
        self, runtime: CtronicsRuntime, entry: ConfigEntry, host: str
    ) -> None:
        assert runtime.watcher is not None
        self._watcher = runtime.watcher
        self._attr_unique_id = f"{entry.entry_id}_person_detected"
        self._attr_device_info = build_device_info(entry, host)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._watcher.async_add_listener(self.async_write_ha_state))

    @property
    def is_on(self) -> bool:
        return self._watcher.detected

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "last_detected": self._watcher.last_detected,
            "last_image": str(self._watcher.latest_file)
            if self._watcher.latest_file
            else None,
        }
