"""Number entities: AI-detection threshold and IRCut switching time."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IRCUT_MAX, IRCUT_MIN
from .coordinator import CtronicsCoordinator
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: CtronicsCoordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]
    async_add_entities(
        [
            CtronicsThresholdNumber(coordinator, entry, host),
            CtronicsIrCutNumber(coordinator, entry, host),
        ]
    )


class CtronicsThresholdNumber(CoordinatorEntity[CtronicsCoordinator], NumberEntity):
    """Schwelle (1-100) für die KI-Personenerkennung."""

    _attr_has_entity_name = True
    entity_description = NumberEntityDescription(
        key="detection_threshold",
        translation_key="detection_threshold",
        icon="mdi:tune-variant",
        native_min_value=1,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
    )

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_detection_threshold"
        self._attr_device_info = build_device_info(entry, host)

    @property
    def native_value(self) -> float:
        return float(self.coordinator.data["smd_gthresh"])

    async def async_set_native_value(self, value: float) -> None:
        data = self.coordinator.data
        await self.coordinator.client.set_smd_threshold(
            threshold=int(value),
            smd_rect=data.get("smd_rect", "0"),
            smd_type=data.get("smd_type", "0"),
        )
        await self.coordinator.async_request_refresh()


class CtronicsIrCutNumber(CoordinatorEntity[CtronicsCoordinator], NumberEntity):
    """IRCut-Schaltzeit (1-1024) — höherer Wert = längere Umschaltzeit."""

    _attr_has_entity_name = True
    entity_description = NumberEntityDescription(
        key="ircut_value",
        translation_key="ircut_value",
        icon="mdi:theme-light-dark",
        native_min_value=IRCUT_MIN,
        native_max_value=IRCUT_MAX,
        native_step=1,
        mode=NumberMode.BOX,
    )

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_ircut_value"
        self._attr_device_info = build_device_info(entry, host)
        # Kept so the entity still shows a sensible value if this firmware
        # has no read command for it (only the write side is confirmed).
        self._local_value: int | None = None

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get("ircut_value")
        if value is None:
            value = self._local_value
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        self._local_value = int(value)
        await self.coordinator.client.set_ircut_switch_value(int(value))
        await self.coordinator.async_request_refresh()
