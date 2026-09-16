"""Select entities: IR LED control and the stored PTZ speed."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    IR_MODES,
    PTZ_SPEED_BY_INDEX,
    PTZ_SPEED_MODES,
    PTZ_SPEED_TO_INDEX,
)
from .coordinator import CtronicsCoordinator
from .models import CtronicsRuntime
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime: CtronicsRuntime = hass.data[DOMAIN][entry.entry_id]
    coordinator = runtime.coordinator
    host = entry.data[CONF_HOST]
    async_add_entities(
        [
            CtronicsIrModeSelect(coordinator, entry, host),
            CtronicsPtzSpeedSelect(coordinator, entry, host),
        ]
    )


class CtronicsIrModeSelect(CoordinatorEntity[CtronicsCoordinator], SelectEntity):
    """IR-LED-Steuerung: auto / open (on) / close (off)."""

    _attr_has_entity_name = True
    entity_description = SelectEntityDescription(
        key="ir_mode", translation_key="ir_mode", icon="mdi:led-on"
    )

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_ir_mode"
        self._attr_options = list(IR_MODES)
        self._attr_device_info = build_device_info(entry, host)

    @property
    def current_option(self) -> str | None:
        mode = self.coordinator.data.get("infrared_mode")
        return mode if mode in IR_MODES else None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.set_infrared_mode(option)
        await self.coordinator.async_request_refresh()


class CtronicsPtzSpeedSelect(CoordinatorEntity[CtronicsCoordinator], SelectEntity):
    """PTZ-Geschwindigkeit: Schnell / Mittel / Langsam.

    This is the camera's own stored setting, the same dropdown its interface
    shows under Erweitert -> Terminal. One control sets both axes, matching
    what the camera does itself.
    """

    _attr_has_entity_name = True
    entity_description = SelectEntityDescription(
        key="ptz_speed_mode", translation_key="ptz_speed_mode", icon="mdi:speedometer"
    )

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_ptz_speed_mode"
        self._attr_options = list(PTZ_SPEED_MODES)
        self._attr_device_info = build_device_info(entry, host)

    @property
    def current_option(self) -> str | None:
        index = self.coordinator.data.get("ptz_speed_index")
        return PTZ_SPEED_BY_INDEX.get(index)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.set_ptz_speed_index(PTZ_SPEED_TO_INDEX[option])
        await self.coordinator.async_request_refresh()
