"""Button entities: PTZ presets, and saving a snapshot to disk."""
from __future__ import annotations

import logging
import os

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util, slugify

from .api import CtronicsApiError
from .const import (
    CONF_PRESET_COUNT,
    CONF_SNAPSHOT_FOLDER,
    DEFAULT_PRESET_COUNT,
    DEFAULT_SNAPSHOT_FOLDER,
    DOMAIN,
    EVENT_SNAPSHOT_SAVED,
    MAX_PRESET_COUNT,
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
    preset_count = min(
        entry.options.get(CONF_PRESET_COUNT, DEFAULT_PRESET_COUNT), MAX_PRESET_COUNT
    )
    snapshot_folder = (
        entry.options.get(CONF_SNAPSHOT_FOLDER) or DEFAULT_SNAPSHOT_FOLDER
    ).strip()

    entities: list[ButtonEntity] = [
        CtronicsPresetButton(coordinator, entry, host, number)
        for number in range(preset_count)
    ]
    entities.append(
        CtronicsSaveSnapshotButton(coordinator, entry, host, snapshot_folder)
    )
    async_add_entities(entities)


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


class CtronicsSaveSnapshotButton(ButtonEntity):
    """Grabs a fresh still from the camera and writes it to disk.

    The default target sits under /media, which Home Assistant's own Medien
    panel browses — so a saved image can be looked at and downloaded from the
    UI without touching configuration.yaml. (The built-in ``camera.snapshot``
    service can only write to folders listed in ``allowlist_external_dirs``;
    this button has no such requirement.)
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CtronicsCoordinator,
        entry: ConfigEntry,
        host: str,
        folder: str,
    ) -> None:
        self.coordinator = coordinator
        self.entity_description = ButtonEntityDescription(
            key="save_snapshot",
            translation_key="save_snapshot",
            icon="mdi:camera-plus",
        )
        self._attr_unique_id = f"{entry.entry_id}_save_snapshot"
        self._attr_device_info = build_device_info(entry, host)
        self._entry_id = entry.entry_id
        self._folder = folder
        self._file_stub = slugify(entry.title) or "ctronics"

    async def async_press(self) -> None:
        try:
            image = await self.coordinator.client.get_snapshot(fresh=True)
        except CtronicsApiError as err:
            raise HomeAssistantError(f"Snapshot failed: {err}") from err

        # Local time, so the file name matches what the user sees in HA.
        stamp = dt_util.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(self._folder, f"{self._file_stub}_{stamp}.jpg")

        try:
            await self.hass.async_add_executor_job(_write_image, path, image)
        except OSError as err:
            raise HomeAssistantError(f"Could not write {path}: {err}") from err

        _LOGGER.info("Saved snapshot to %s (%d bytes)", path, len(image))
        self.hass.bus.async_fire(
            EVENT_SNAPSHOT_SAVED,
            {"entry_id": self._entry_id, "path": path, "size": len(image)},
        )


def _write_image(path: str, data: bytes) -> None:
    """Blocking write, run in the executor."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)
