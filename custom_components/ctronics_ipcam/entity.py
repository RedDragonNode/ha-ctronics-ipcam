"""Shared helpers for all Ctronics entities."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def build_device_info(entry: ConfigEntry, host: str) -> DeviceInfo:
    """One device that every entity of this config entry belongs to."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Ctronics",
        model="Hi3510-based IP Camera",
        configuration_url=f"http://{host}/web/admin.html",
    )
