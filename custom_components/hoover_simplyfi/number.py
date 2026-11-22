"""Ritardo di partenza, in ore, per il prossimo avvio da remoto."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DELAY_MAX_HOURS
from .coordinator import SimplyFiConfigEntry, SimplyFiCoordinator
from .entity import SimplyFiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimplyFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Crea il numero del ritardo (solo con i comandi attivati)."""
    async_add_entities([SimplyFiDelayNumber(entry.runtime_data)])


class SimplyFiDelayNumber(SimplyFiEntity, NumberEntity):
    """Ore di ritardo prima della partenza; 0 significa avvio immediato."""

    _attr_native_min_value = 0
    _attr_native_max_value = DELAY_MAX_HOURS
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SimplyFiCoordinator) -> None:
        super().__init__(coordinator, "delay")

    @property
    def available(self) -> bool:
        return self.coordinator.can_command

    @property
    def native_value(self) -> int:
        return self.coordinator.delay_hours

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.delay_hours = int(value)
        self.coordinator.async_update_listeners()
