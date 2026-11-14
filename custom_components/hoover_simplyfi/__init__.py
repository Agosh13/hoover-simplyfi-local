"""Integrazione locale per lavatrici Hoover/Candy simply-Fi."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import SimplyFiConfigEntry, SimplyFiCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: SimplyFiConfigEntry) -> bool:
    """Configura la lavatrice da una voce di configurazione."""
    coordinator = SimplyFiCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SimplyFiConfigEntry) -> bool:
    """Rimuove la voce di configurazione."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
