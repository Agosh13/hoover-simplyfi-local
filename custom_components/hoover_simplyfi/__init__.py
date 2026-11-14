"""Integrazione locale per lavatrici Hoover/Candy simply-Fi."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import SimplyFiConfigEntry, SimplyFiCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]
CONTROL_PLATFORMS = [Platform.BUTTON, Platform.SELECT]


def _platforms(coordinator: SimplyFiCoordinator) -> list[Platform]:
    if coordinator.control_enabled:
        return PLATFORMS + CONTROL_PLATFORMS
    return PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: SimplyFiConfigEntry) -> bool:
    """Configura la lavatrice da una voce di configurazione."""
    coordinator = SimplyFiCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload_on_options))
    await hass.config_entries.async_forward_entry_setups(entry, _platforms(coordinator))
    return True


async def _async_reload_on_options(
    hass: HomeAssistant, entry: SimplyFiConfigEntry
) -> None:
    """Ricarica quando cambiano le opzioni (es. il modello)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: SimplyFiConfigEntry) -> bool:
    """Rimuove la voce di configurazione."""
    return await hass.config_entries.async_unload_platforms(
        entry, _platforms(entry.runtime_data)
    )
