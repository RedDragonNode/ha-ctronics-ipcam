"""Config flow for the Ctronics IP Camera integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CtronicsApiError, CtronicsAuthError, CtronicsClient
from .const import (
    CONF_ALARM_FOLDER,
    CONF_ALARM_PREFIX,
    CONF_OFF_DELAY,
    DEFAULT_ALARM_PREFIX,
    CONF_PRESET_COUNT,
    DEFAULT_OFF_DELAY,
    DEFAULT_PORT,
    DEFAULT_PRESET_COUNT,
    DOMAIN,
    MAX_PRESET_COUNT,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_ALARM_FOLDER, default=""): str,
    }
)


class CtronicsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ctronics IP Camera."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = CtronicsClient(
                session=session,
                host=user_input[CONF_HOST],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                port=user_input[CONF_PORT],
            )
            try:
                # Cheap read-only call used purely to confirm host/auth work.
                await client.get_smartrack_enabled()
            except CtronicsAuthError:
                errors["base"] = "invalid_auth"
            except CtronicsApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating Ctronics camera")
                errors["base"] = "unknown"
            else:
                alarm_folder = (user_input.get(CONF_ALARM_FOLDER) or "").strip()
                data = {
                    key: value
                    for key, value in user_input.items()
                    if key != CONF_ALARM_FOLDER
                }
                return self.async_create_entry(
                    title=f"Ctronics IPCAM ({user_input[CONF_HOST]})",
                    data=data,
                    options={
                        CONF_PRESET_COUNT: DEFAULT_PRESET_COUNT,
                        CONF_ALARM_FOLDER: alarm_folder,
                        CONF_OFF_DELAY: DEFAULT_OFF_DELAY,
                        CONF_ALARM_PREFIX: DEFAULT_ALARM_PREFIX,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return CtronicsOptionsFlow(config_entry)


class CtronicsOptionsFlow(OptionsFlow):
    """Preset button count, alarm folder and how long detection stays on."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        if user_input is not None:
            user_input[CONF_ALARM_FOLDER] = (
                user_input.get(CONF_ALARM_FOLDER) or ""
            ).strip()
            return self.async_create_entry(data=user_input)

        options = self._config_entry.options
        schema = vol.Schema(
            {
                # The camera stores at most 8 presets, so anything above that
                # would only create buttons that can never work.
                vol.Optional(
                    CONF_PRESET_COUNT,
                    default=options.get(CONF_PRESET_COUNT, DEFAULT_PRESET_COUNT),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=MAX_PRESET_COUNT)),
                vol.Optional(
                    CONF_ALARM_FOLDER,
                    default=options.get(CONF_ALARM_FOLDER, ""),
                ): str,
                vol.Optional(
                    CONF_OFF_DELAY,
                    default=options.get(CONF_OFF_DELAY, DEFAULT_OFF_DELAY),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=600)),
                vol.Optional(
                    CONF_ALARM_PREFIX,
                    default=options.get(CONF_ALARM_PREFIX, DEFAULT_ALARM_PREFIX),
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
