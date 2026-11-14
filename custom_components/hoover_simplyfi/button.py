"""Pulsanti di avvio e stop."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SimplyFiConfigEntry, SimplyFiCoordinator
from .entity import SimplyFiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimplyFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Crea i pulsanti (solo con i comandi attivati)."""
    coordinator = entry.runtime_data
    async_add_entities([SimplyFiStartButton(coordinator), SimplyFiStopButton(coordinator)])


class SimplyFiStartButton(SimplyFiEntity, ButtonEntity):
    """Avvia il programma selezionato."""

    def __init__(self, coordinator: SimplyFiCoordinator) -> None:
        super().__init__(coordinator, "start")

    @property
    def available(self) -> bool:
        return self.coordinator.selected_program is not None

    async def async_press(self) -> None:
        await self.coordinator.async_start()


class SimplyFiStopButton(SimplyFiEntity, ButtonEntity):
    """Ferma il ciclo in corso."""

    def __init__(self, coordinator: SimplyFiCoordinator) -> None:
        super().__init__(coordinator, "stop")

    @property
    def available(self) -> bool:
        return self.coordinator.data.online

    async def async_press(self) -> None:
        await self.coordinator.async_stop()
