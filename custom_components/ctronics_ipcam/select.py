"""Select entity for the camera's IR LED control (Auto / on / off)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IR_MODES
from .coordinator import CtronicsCoordinator
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: CtronicsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CtronicsIrModeSelect(coordinator, entry, entry.data[CONF_HOST])])


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
