"""Button entities: one per configured PTZ preset, to move the camera there."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_PRESET_COUNT, DEFAULT_PRESET_COUNT, DOMAIN, MAX_PRESET_COUNT
from .coordinator import CtronicsCoordinator
from .models import CtronicsRuntime
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime: CtronicsRuntime = hass.data[DOMAIN][entry.entry_id]
    coordinator = runtime.coordinator
    host = entry.data[CONF_HOST]
    preset_count = min(
        entry.options.get(CONF_PRESET_COUNT, DEFAULT_PRESET_COUNT), MAX_PRESET_COUNT
    )

    async_add_entities(
        [
            CtronicsPresetButton(coordinator, entry, host, number)
            for number in range(preset_count)
        ]
    )


class CtronicsPresetButton(ButtonEntity):
    """Fährt ein gespeichertes PTZ-Preset an.

    Preset-Nummerierung folgt der Kamera: sie zählt intern ab 0, während die
    Weboberfläche "Voreinstellung 1", "2", ... anzeigt — Voreinstellung 1
    entspricht also -number=0. Die Kamera kann maximal 8 Presets speichern.

    Die Kamera bietet keinen Befehl, um abzufragen welche Presets belegt sind
    (nachgeprüft: getpresetattr / getpreset / getptzpresetattr existieren
    nicht). Deshalb wird die Anzahl der Buttons in den Integrations-Optionen
    eingestellt statt automatisch erkannt.
    """

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str, number: int
    ) -> None:
        self.coordinator = coordinator
        self._number = number
        self.entity_description = ButtonEntityDescription(
            key=f"preset_{number}",
            translation_key="preset",
            icon="mdi:crosshairs",
        )
        # The button name comes from translations/<lang>.json; the preset
        # number is filled into the {number} placeholder, so the label follows
        # the user's Home Assistant language instead of being hard-coded.
        self._attr_translation_placeholders = {"number": str(number + 1)}
        self._attr_unique_id = f"{entry.entry_id}_preset_{number}"
        self._attr_device_info = build_device_info(entry, host)

    async def async_press(self) -> None:
        await self.coordinator.client.ptz_preset_goto(self._number)
