"""Switch entities for the Ctronics IP Camera integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CtronicsCoordinator
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: CtronicsCoordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]
    async_add_entities(
        [
            CtronicsAiDetectionSwitch(coordinator, entry, host),
            CtronicsAutoTrackingSwitch(coordinator, entry, host),
        ]
    )


class _CtronicsSwitchBase(CoordinatorEntity[CtronicsCoordinator], SwitchEntity):
    """Shared plumbing: device info + coordinator wiring."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str, key: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = build_device_info(entry, host)


class CtronicsAiDetectionSwitch(_CtronicsSwitchBase):
    """KI-Personenerkennung (Intelligente Identifizierung) an/aus."""

    entity_description = SwitchEntityDescription(
        key="ai_detection", translation_key="ai_detection", icon="mdi:account-eye"
    )

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__(coordinator, entry, host, "ai_detection")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data["smd_enabled"])

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_smd_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_smd_enabled(False)
        await self.coordinator.async_request_refresh()


class CtronicsAutoTrackingSwitch(_CtronicsSwitchBase):
    """Auto-Tracking (Smart Track) an/aus."""

    entity_description = SwitchEntityDescription(
        key="auto_tracking", translation_key="auto_tracking", icon="mdi:crosshairs-gps"
    )

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__(coordinator, entry, host, "auto_tracking")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data["smartrack_enabled"])

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_smartrack_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_smartrack_enabled(False)
        await self.coordinator.async_request_refresh()
