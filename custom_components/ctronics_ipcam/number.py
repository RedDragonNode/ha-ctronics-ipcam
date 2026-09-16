"""Number entities: detection threshold, IRCut time and the preset slot."""
from __future__ import annotations

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IRCUT_MAX, IRCUT_MIN, MAX_PRESET_COUNT
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
            CtronicsThresholdNumber(coordinator, entry, host),
            CtronicsIrCutNumber(coordinator, entry, host),
            CtronicsPresetSlotNumber(runtime, entry, host),
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


class CtronicsLocalNumber(RestoreNumber):
    """A number the camera doesn't store — Home Assistant keeps it instead.

    The camera's own interface treats the preset slot as a plain form field:
    it is read from the page, never from the device, and there is no command
    to ask for it. So the value lives in the runtime object and is restored
    from Home Assistant's own state on restart.
    """

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_should_poll = False

    def __init__(self, runtime: CtronicsRuntime, entry: ConfigEntry, host: str) -> None:
        self._runtime = runtime
        self._attr_unique_id = f"{entry.entry_id}_{self.entity_description.key}"
        self._attr_device_info = build_device_info(entry, host)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last is not None and last.native_value is not None:
            self._apply(int(last.native_value))

    def _apply(self, value: int) -> None:
        raise NotImplementedError

    async def async_set_native_value(self, value: float) -> None:
        self._apply(int(value))
        self.async_write_ha_state()


class CtronicsPresetSlotNumber(CtronicsLocalNumber):
    """Which preset the save/delete buttons act on — 1-8, as the camera counts."""

    entity_description = NumberEntityDescription(
        key="preset_slot",
        translation_key="preset_slot",
        icon="mdi:numeric",
        native_min_value=1,
        native_max_value=MAX_PRESET_COUNT,
        native_step=1,
        mode=NumberMode.BOX,
    )

    @property
    def native_value(self) -> float:
        return float(self._runtime.preset_slot)

    def _apply(self, value: int) -> None:
        self._runtime.preset_slot = value
