# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Config flow for the local Energy Ingest API."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnergyApi, EnergyApiError, EnergyAuthError
from .const import CONF_TOKEN, DEFAULT_URL, DOMAIN
from .statistics_sync_settings import (
    CONF_SYNC_ENABLED, DEFAULT_SYNC_ENABLED,
    CONF_SYNC_HOURS, CONF_SYNC_STARTUP, DEFAULT_SYNC_HOURS,
    DEFAULT_SYNC_STARTUP, SYNC_INTERVAL_CHOICES,
)


def connection_schema(default_url: str = DEFAULT_URL):
    """Build a user-facing connection form."""
    return vol.Schema(
        {
            vol.Required(CONF_URL, default=default_url): str,
            vol.Required(CONF_TOKEN): str,
        }
    )


class EnergyUsageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Connect to an Energy Ingest instance using a bearer token."""

    VERSION = 1

    @staticmethod
    def _meter_summary(meters):
        """Display authoritative meter IDs without inferring associations."""
        if not meters:
            return "No physical meters registered yet."
        return "; ".join(
            f"{meter['display_name']} (ID {meter['id']}, "
            f"{'Electricity' if meter['commodity'] == 1 else 'Gas'})"
            for meter in meters
            if isinstance(meter, dict)
            and type(meter.get("id")) is int
            and meter.get("commodity") in (1, 7)
            and isinstance(meter.get("display_name"), str)
        ) or "No supported physical meters registered yet."

    @staticmethod
    def async_get_options_flow(config_entry):
        """Provide Home Assistant integration-specific preferences."""
        return EnergyUsageOptionsFlow()

    async def _validate(self, url: str, token: str):
        """Confirm credentials and receive the available meter list."""
        api = EnergyApi(async_get_clientsession(self.hass), url, token)
        return await api.meters()

    async def async_step_user(self, user_input=None):
        """Set up a new local API connection."""
        errors = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            token = user_input[CONF_TOKEN]
            try:
                meters = await self._validate(url, token)
            except EnergyAuthError:
                errors["base"] = "invalid_auth"
            except (EnergyApiError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                self._pending_connection = (url, token)
                self._meter_names = self._meter_summary(meters)
                return await self.async_step_confirm_meters()
        return self.async_show_form(
            step_id="user",
            data_schema=connection_schema(),
            errors=errors,
        )

    async def async_step_confirm_meters(self, user_input=None):
        """Make discovered physical-meter identities visible at setup."""
        if not hasattr(self, "_pending_connection"):
            return await self.async_step_user()
        if user_input is not None and user_input.get("confirm_meters"):
            url, token = self._pending_connection
            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Energy Usage",
                data={CONF_URL: url, CONF_TOKEN: token},
            )
        return self.async_show_form(
            step_id="confirm_meters",
            data_schema=vol.Schema({
                vol.Required("confirm_meters", default=False): bool,
            }),
            description_placeholders={"meters": self._meter_names},
        )

    async def async_step_reauth(self, entry_data):
        """Start a reauthentication flow for an existing entry."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Replace a revoked or rotated API token."""
        errors = {}
        if user_input is not None:
            url = self._get_reauth_entry().data[CONF_URL]
            try:
                await self._validate(url, user_input[CONF_TOKEN])
            except EnergyAuthError:
                errors["base"] = "invalid_auth"
            except (EnergyApiError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={CONF_TOKEN: user_input[CONF_TOKEN]},
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )


    async def async_step_reconfigure(self, user_input=None):
        """Allow changing the API endpoint without removing the entry."""
        entry = self._get_reconfigure_entry()
        errors = {}

        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            token = user_input[CONF_TOKEN]

            try:
                await self._validate(url, token)
            except EnergyAuthError:
                errors["base"] = "invalid_auth"
            except (EnergyApiError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                # A server URL is the current instance identity.
                # Preserve that identity only after validation.
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_URL: url, CONF_TOKEN: token},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=entry.data[CONF_URL],
                    ): str,
                    vol.Required(CONF_TOKEN): str,
                }
            ),
            errors=errors,
        )

class EnergyUsageOptionsFlow(config_entries.OptionsFlow):
    """Configure automatic synchronization per integration entry."""

    async def async_step_init(self, user_input=None):
        """Persist the interval and startup preference."""
        if user_input is not None:
            hours = int(user_input[CONF_SYNC_HOURS])
            if hours not in SYNC_INTERVAL_CHOICES:
                raise ValueError("Unsupported sync interval")

            return self.async_create_entry(
                title="",
                data={
                    CONF_SYNC_ENABLED: user_input[CONF_SYNC_ENABLED],
                    CONF_SYNC_HOURS: hours,
                    CONF_SYNC_STARTUP: user_input[CONF_SYNC_STARTUP],
                },
            )

        options = self.config_entry.options
        enabled = options.get(CONF_SYNC_ENABLED, DEFAULT_SYNC_ENABLED)
        hours = options.get(
            CONF_SYNC_HOURS, DEFAULT_SYNC_HOURS
        )
        startup = options.get(
            CONF_SYNC_STARTUP, DEFAULT_SYNC_STARTUP
        )

        try:
            meter_list = await EnergyApi(
                async_get_clientsession(self.hass),
                self.config_entry.data[CONF_URL],
                self.config_entry.data[CONF_TOKEN],
            ).meters()
            meter_summary = EnergyUsageConfigFlow._meter_summary(meter_list)
        except EnergyApiError:
            meter_summary = "Meter inventory temporarily unavailable."
        return self.async_show_form(
            step_id="init",
            description_placeholders={"meters": meter_summary},
            data_schema=vol.Schema({
                vol.Required(CONF_SYNC_ENABLED, default=enabled): bool,
                vol.Required(
                    CONF_SYNC_HOURS,
                    default=str(hours),
                ): vol.In({
                    str(key): label
                    for key, label in SYNC_INTERVAL_CHOICES.items()
                }),
                vol.Required(
                    CONF_SYNC_STARTUP,
                    default=startup,
                ): bool,
            }),
        )
