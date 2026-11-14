"""Sensori binari della lavatrice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SimplyFiConfigEntry, SimplyFiCoordinator, WasherData
from .entity import SimplyFiEntity


@dataclass(frozen=True, kw_only=True)
class SimplyFiBinaryDescription(BinarySensorEntityDescription):
    """Descrizione di un sensore binario."""

    value_fn: Callable[[WasherData], bool]


BINARY_SENSORS: tuple[SimplyFiBinaryDescription, ...] = (
    SimplyFiBinaryDescription(
        key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.running,
    ),
    SimplyFiBinaryDescription(
        key="remote_control",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.remote_control,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimplyFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Crea i sensori binari."""
    coordinator = entry.runtime_data
    async_add_entities(SimplyFiBinarySensor(coordinator, d) for d in BINARY_SENSORS)


class SimplyFiBinarySensor(SimplyFiEntity, BinarySensorEntity):
    """Sensore binario della lavatrice."""

    entity_description: SimplyFiBinaryDescription

    def __init__(
        self, coordinator: SimplyFiCoordinator, description: SimplyFiBinaryDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)
