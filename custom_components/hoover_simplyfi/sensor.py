"""Sensori della lavatrice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_MODEL,
    ERROR_CODES,
    MACHINE_STATES,
    MODEL_GENERIC,
    PHASES,
    PROGRAM_SETS,
    STATE_OFF,
)
from .coordinator import SimplyFiConfigEntry, SimplyFiCoordinator, WasherData
from .entity import SimplyFiEntity


@dataclass(frozen=True, kw_only=True)
class SimplyFiSensorDescription(SensorEntityDescription):
    """Descrizione di un sensore con la funzione che ne estrae il valore."""

    value_fn: Callable[[WasherData], Any]


SENSORS: tuple[SimplyFiSensorDescription, ...] = (
    SimplyFiSensorDescription(
        key="state",
        device_class=SensorDeviceClass.ENUM,
        options=[STATE_OFF, *dict.fromkeys(MACHINE_STATES.values())],
        value_fn=lambda d: d.state,
    ),
    SimplyFiSensorDescription(
        key="phase",
        device_class=SensorDeviceClass.ENUM,
        options=list(PHASES.values()),
        value_fn=lambda d: d.phase,
    ),
    SimplyFiSensorDescription(
        key="remaining_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda d: d.remaining_minutes,
    ),
    SimplyFiSensorDescription(
        key="end_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.end_time,
    ),
    SimplyFiSensorDescription(
        key="program",
        value_fn=lambda d: d.program,
    ),
    SimplyFiSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.temperature,
    ),
    SimplyFiSensorDescription(
        key="spin_speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        value_fn=lambda d: d.spin_speed,
    ),
    SimplyFiSensorDescription(
        key="error",
        device_class=SensorDeviceClass.ENUM,
        options=["none", "unknown", *dict.fromkeys(ERROR_CODES.values())],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.error,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimplyFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Crea i sensori."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [SimplyFiSensor(coordinator, d) for d in SENSORS]
    programs = PROGRAM_SETS.get(entry.options.get(CONF_MODEL, MODEL_GENERIC))
    if programs:
        entities.append(SimplyFiProgramNameSensor(coordinator, programs))
    async_add_entities(entities)


class SimplyFiSensor(SimplyFiEntity, SensorEntity):
    """Sensore della lavatrice."""

    entity_description: SimplyFiSensorDescription

    def __init__(
        self, coordinator: SimplyFiCoordinator, description: SimplyFiSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "error":
            return None
        return {"code": self.coordinator.data.error_code}


class SimplyFiProgramNameSensor(SimplyFiEntity, SensorEntity):
    """Nome del programma, per i modelli di cui si conosce la manopola."""

    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self, coordinator: SimplyFiCoordinator, programs: dict[int, str]
    ) -> None:
        super().__init__(coordinator, "program_name")
        self._programs = programs
        self._attr_options = list(dict.fromkeys(programs.values()))

    @property
    def native_value(self) -> str | None:
        position = self.coordinator.data.program
        return None if position is None else self._programs.get(position)
