"""Configurazione da interfaccia: basta l'indirizzo IP della lavatrice."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import SimplyFiClient, SimplyFiConnectionError, SimplyFiProtocolError
from .const import (
    CONF_KEY,
    CONF_MODEL,
    CONF_REMTIME_SECONDS,
    DOMAIN,
    MODEL_GENERIC,
    PROGRAM_SETS,
)

MODEL_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[MODEL_GENERIC, *PROGRAM_SETS],
        mode=SelectSelectorMode.DROPDOWN,
        translation_key="model",
    )
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_MODEL, default=MODEL_GENERIC): MODEL_SELECTOR,
        vol.Optional(CONF_REMTIME_SECONDS, default=False): bool,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {vol.Required(CONF_MODEL, default=MODEL_GENERIC): MODEL_SELECTOR}
)


class SimplyFiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Flusso di configurazione."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SimplyFiOptionsFlow()

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
                    options={CONF_MODEL: user_input[CONF_MODEL]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
            errors=errors,
        )


class SimplyFiOptionsFlow(OptionsFlow):
    """Opzioni: scelta del modello, da cui dipendono i nomi dei programmi."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
