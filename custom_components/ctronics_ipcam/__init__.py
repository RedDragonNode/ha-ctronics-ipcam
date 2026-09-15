"""The Ctronics IP Camera integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .alarm_watcher import AlarmFolderWatcher
from .api import CtronicsClient
from .const import (
    CONF_ALARM_FOLDER,
    CONF_ALARM_PREFIX,
    CONF_OFF_DELAY,
    DEFAULT_ALARM_PREFIX,
    DEFAULT_OFF_DELAY,
    DEFAULT_PORT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import CtronicsCoordinator
from .models import CtronicsRuntime


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ctronics IP Camera from a config entry."""
    session = async_get_clientsession(hass)
    client = CtronicsClient(
        session=session,
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
    )

    coordinator = CtronicsCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    runtime = CtronicsRuntime(coordinator=coordinator)

    alarm_folder = entry.options.get(CONF_ALARM_FOLDER)
    if alarm_folder:
        runtime.watcher = AlarmFolderWatcher(
            hass,
            folder=alarm_folder,
            off_delay=entry.options.get(CONF_OFF_DELAY, DEFAULT_OFF_DELAY),
            alarm_prefix=entry.options.get(CONF_ALARM_PREFIX, DEFAULT_ALARM_PREFIX),
        )
        await runtime.watcher.async_start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = runtime

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change (preset count, alarm folder, off delay)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        runtime: CtronicsRuntime = hass.data[DOMAIN].pop(entry.entry_id)
        if runtime.watcher is not None:
            runtime.watcher.async_stop()
    return unload_ok
