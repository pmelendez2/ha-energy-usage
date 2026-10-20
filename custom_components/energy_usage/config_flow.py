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
                await self._validate(url, token)
            except EnergyAuthError:
                errors["base"] = "invalid_auth"
            except (EnergyApiError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Energy Usage",
                    data={CONF_URL: url, CONF_TOKEN: token},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=connection_schema(),
            errors=errors,
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
