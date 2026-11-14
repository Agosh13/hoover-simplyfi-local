"""Scelta del programma e della centrifuga per l'avvio da remoto."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import SPIN_CHOICES, SPIN_DEFAULT
from .coordinator import SimplyFiConfigEntry, SimplyFiCoordinator
from .entity import SimplyFiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimplyFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Crea i selettori (solo con i comandi attivati)."""
    coordinator = entry.runtime_data
    async_add_entities(
        [SimplyFiProgramSelect(coordinator), SimplyFiSpinSelect(coordinator)]
    )


class _ControlSelect(SimplyFiEntity, SelectEntity):
    """Selettore utilizzabile solo con la macchina in controllo remoto."""

    @property
    def available(self) -> bool:
        return self.coordinator.can_command


class SimplyFiProgramSelect(_ControlSelect):
    """Programma da avviare: sceglierlo lo seleziona sulla macchina, senza avviarla."""

    def __init__(self, coordinator: SimplyFiCoordinator) -> None:
        super().__init__(coordinator, "program_select")
        self._by_name = {name: pos for pos, name in coordinator.programs.items()}
        self._attr_options = list(self._by_name)

    @property
    def current_option(self) -> str | None:
        position = self.coordinator.selected_program
        return None if position is None else self.coordinator.programs[position]

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_select_program(self._by_name[option])


class SimplyFiSpinSelect(_ControlSelect):
    """Centrifuga per il prossimo avvio; torna a "predefinita" a ogni cambio programma."""

    _attr_options = [SPIN_DEFAULT, *(str(s * 100) for s in SPIN_CHOICES)]

    def __init__(self, coordinator: SimplyFiCoordinator) -> None:
        super().__init__(coordinator, "spin_select")

    @property
    def current_option(self) -> str:
        choice = self.coordinator.spin_choice
        return SPIN_DEFAULT if choice is None else str(choice * 100)

    async def async_select_option(self, option: str) -> None:
        self.coordinator.spin_choice = (
            None if option == SPIN_DEFAULT else int(option) // 100
        )
        self.coordinator.async_update_listeners()
