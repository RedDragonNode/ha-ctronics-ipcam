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
    CONF_PTZ_STEP_MS,
    CONF_SNAPSHOT_FOLDER,
    DEFAULT_PTZ_SPEED_MODE,
    DEFAULT_PTZ_STEP_MS,
    DEFAULT_SNAPSHOT_FOLDER,
    DOMAIN,
    EVENT_SNAPSHOT_SAVED,
    MAX_PRESET_COUNT,
    PTZ_SPEED_BY_INDEX,
    PTZ_SPEED_MODE_TO_STEP_SPEED,
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
    snapshot_folder = (
        entry.options.get(CONF_SNAPSHOT_FOLDER) or DEFAULT_SNAPSHOT_FOLDER
    ).strip()

    step_ms = entry.options.get(CONF_PTZ_STEP_MS, DEFAULT_PTZ_STEP_MS)

    # One button per slot the camera can hold, all disabled out of the box.
    # The camera cannot say which slots are in use (getpresetattr / getpreset
    # / getptzpresetattr all 404), so rather than guess, every button is
    # created and left switched off; the user enables the ones they have
    # actually stored, in Home Assistant's own entity settings.
    entities: list[ButtonEntity] = [
        CtronicsPresetButton(coordinator, entry, host, slot)
        for slot in range(1, MAX_PRESET_COUNT + 1)
    ]
    entities.append(
        CtronicsSaveSnapshotButton(coordinator, entry, host, snapshot_folder)
    )

    # Movement that runs for a moment and then stops on its own. Zoom and
    # focus are deliberately absent: this camera has a fixed lens.
    for key, action, icon in (
        ("ptz_up", "up", "mdi:arrow-up-bold"),
        ("ptz_down", "down", "mdi:arrow-down-bold"),
        ("ptz_left", "left", "mdi:arrow-left-bold"),
        ("ptz_right", "right", "mdi:arrow-right-bold"),
    ):
        entities.append(
            CtronicsPtzStepButton(runtime, entry, host, key, action, icon, step_ms)
        )

    # Fire-and-forget: home re-centres, the scans run until stopped.
    for key, action, icon in (
        ("ptz_home", "home", "mdi:home-map-marker"),
        ("ptz_scan_h", "hscan", "mdi:arrow-left-right"),
        ("ptz_scan_v", "vscan", "mdi:arrow-up-down"),
        ("ptz_stop", "stop", "mdi:stop-circle-outline"),
    ):
        entities.append(
            CtronicsPtzActionButton(runtime, entry, host, key, action, icon)
        )

    entities.append(CtronicsPresetSaveButton(runtime, entry, host))
    entities.append(CtronicsPresetDeleteButton(runtime, entry, host))

    async_add_entities(entities)


class CtronicsPresetButton(ButtonEntity):
    """Fährt ein gespeichertes PTZ-Preset an.

    Preset-Nummerierung folgt der Kamera: sie zählt intern ab 0, während die
    Weboberfläche "Voreinstellung 1", "2", ... anzeigt — Voreinstellung 1
    entspricht also -number=0. Die Kamera speichert bis zu 64 Positionen (am
    Gerät getestet: 64 geht, 65 nicht).

    Die Kamera bietet keinen Befehl, um abzufragen welche Presets belegt sind
    (nachgeprüft: getpresetattr / getpreset / getptzpresetattr existieren
    nicht). Deshalb werden alle 64 Buttons angelegt, aber deaktiviert — der
    Nutzer schaltet in Home Assistant die frei, die er wirklich belegt hat.
    Deaktivierte Entities tauchen nirgends auf und kosten nichts.
    """

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: CtronicsCoordinator, entry: ConfigEntry, host: str, slot: int
    ) -> None:
        self.coordinator = coordinator
        # 1-based, as shown everywhere in the UI; the API call subtracts one.
        self._slot = slot
        self.entity_description = ButtonEntityDescription(
            key=f"preset_{slot}",
            translation_key="preset",
            icon="mdi:crosshairs",
        )
        # The button name comes from translations/<lang>.json; the preset
        # number is filled into the {number} placeholder, so the label follows
        # the user's Home Assistant language instead of being hard-coded.
        self._attr_translation_placeholders = {"number": str(slot)}
        self._attr_unique_id = f"{entry.entry_id}_preset_{slot - 1}"
        self._attr_device_info = build_device_info(entry, host)

    async def async_press(self) -> None:
        await self.coordinator.client.ptz_preset_goto(self._slot - 1)


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


class CtronicsPtzButtonBase(ButtonEntity):
    """Shared wiring for every PTZ button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        runtime: CtronicsRuntime,
        entry: ConfigEntry,
        host: str,
        key: str,
        icon: str,
    ) -> None:
        self._runtime = runtime
        self.entity_description = ButtonEntityDescription(
            key=key, translation_key=key, icon=icon
        )
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = build_device_info(entry, host)

    @property
    def _client(self):
        return self._runtime.coordinator.client

    @property
    def _step_speed(self) -> int:
        """-speed for ptzctrl.cgi, derived from the stored speed mode."""
        index = self._runtime.coordinator.data.get("ptz_speed_index")
        mode = PTZ_SPEED_BY_INDEX.get(index, DEFAULT_PTZ_SPEED_MODE)
        return PTZ_SPEED_MODE_TO_STEP_SPEED[mode]


class CtronicsPtzStepButton(CtronicsPtzButtonBase):
    """Nudge the camera in one direction, then stop.

    The camera moves for as long as the mouse is held down in its own
    interface. A Home Assistant button has no hold, so the step duration
    from the options stands in for it.
    """

    def __init__(
        self,
        runtime: CtronicsRuntime,
        entry: ConfigEntry,
        host: str,
        key: str,
        action: str,
        icon: str,
        step_ms: int,
    ) -> None:
        super().__init__(runtime, entry, host, key, icon)
        self._action = action
        self._step_ms = step_ms

    async def async_press(self) -> None:
        await self._client.ptz_step(self._action, self._step_speed, self._step_ms)


class CtronicsPtzActionButton(CtronicsPtzButtonBase):
    """A PTZ command the camera's own interface sends without a stop."""

    def __init__(
        self,
        runtime: CtronicsRuntime,
        entry: ConfigEntry,
        host: str,
        key: str,
        action: str,
        icon: str,
    ) -> None:
        super().__init__(runtime, entry, host, key, icon)
        self._action = action

    async def async_press(self) -> None:
        await self._client.ptz_command(self._action, self._step_speed)


class CtronicsPresetSaveButton(CtronicsPtzButtonBase):
    """Store the current position in the preset slot chosen by the number entity."""

    def __init__(
        self, runtime: CtronicsRuntime, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__(runtime, entry, host, "preset_save", "mdi:content-save-cog")

    async def async_press(self) -> None:
        slot = self._runtime.preset_slot
        _LOGGER.info("Saving current position as preset %d", slot)
        # The camera counts from 0 while its interface shows 1-8.
        await self._client.ptz_preset_save(slot - 1)


class CtronicsPresetDeleteButton(CtronicsPtzButtonBase):
    """Clear the preset in the chosen slot."""

    def __init__(
        self, runtime: CtronicsRuntime, entry: ConfigEntry, host: str
    ) -> None:
        super().__init__(runtime, entry, host, "preset_delete", "mdi:delete-forever")

    async def async_press(self) -> None:
        slot = self._runtime.preset_slot
        _LOGGER.info("Deleting preset %d", slot)
        await self._client.ptz_preset_delete(slot - 1)


def _write_image(path: str, data: bytes) -> None:
    """Blocking write, run in the executor."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)
