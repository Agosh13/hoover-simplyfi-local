"""Configurazione da interfaccia: basta l'indirizzo IP della lavatrice."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SimplyFiClient, SimplyFiConnectionError, SimplyFiProtocolError
from .const import CONF_KEY, CONF_REMTIME_SECONDS, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_REMTIME_SECONDS, default=False): bool,
    }
)


class SimplyFiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Flusso di configurazione."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            self._async_abort_entries_match({CONF_HOST: host})
            client = SimplyFiClient(async_get_clientsession(self.hass), host)
            try:
                key = await client.async_recover_key()
                await client.async_status()
            except SimplyFiConnectionError:
                errors["base"] = "cannot_connect"
            except SimplyFiProtocolError:
                errors["base"] = "invalid_device"
            else:
                return self.async_create_entry(
                    title=f"Lavatrice ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_KEY: key,
                        CONF_REMTIME_SECONDS: user_input[CONF_REMTIME_SECONDS],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
            errors=errors,
        )
