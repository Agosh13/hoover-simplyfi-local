"""Coordinatore: interroga la lavatrice e ne interpreta lo stato."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api import SimplyFiClient, SimplyFiError
from .const import (
    CONF_KEY,
    CONF_REMTIME_SECONDS,
    DOMAIN,
    ERROR_CODES,
    MACHINE_STATES,
    OFFLINE_AFTER_FAILURES,
    PHASE_END,
    PHASES,
    RUNNING_MODES,
    SCAN_INTERVAL,
    STATE_FINISHED,
    STATE_IDLE,
    STATE_OFF,
    STATE_REMOTE_READY,
)

_LOGGER = logging.getLogger(__name__)

type SimplyFiConfigEntry = ConfigEntry[SimplyFiCoordinator]

# Scarto oltre il quale l'ora di fine prevista viene ricalcolata.
END_TIME_TOLERANCE = timedelta(seconds=150)


def _int(raw: dict[str, Any], name: str) -> int | None:
    """Intero dal campo; 255 significa "non applicabile"."""
    try:
        value = int(raw[name])
    except (KeyError, TypeError, ValueError):
        return None
    return None if value == 255 else value


@dataclass
class WasherData:
    """Stato interpretato. `online` falso = lavatrice spenta o non raggiungibile."""

    online: bool = False
    raw: dict[str, Any] = field(default_factory=dict)
    remtime_seconds: bool = False
    end_time: datetime | None = None
    # Vero se lo stato "in funzione + fase Fine" segue un lavaggio vero.
    after_run: bool = False

    @property
    def mode(self) -> int | None:
        return _int(self.raw, "MachMd") if self.online else None

    @property
    def _phase_code(self) -> int | None:
        return _int(self.raw, "PrPh") if self.online else None

    @property
    def _cycle_over(self) -> bool:
        """Vero se la macchina dice "in funzione" ma la fase è già "Fine".

        Su una macchina reale MachMd=2 con fase "Fine" e un tempo rimanente
        fasullo non è un lavaggio: è lo stato di riposo in cui la macchina
        aspetta un comando dall'app (manopola su controllo remoto), e compare
        anche riaccendendola dopo la fine di un ciclo.
        """
        return self.mode in RUNNING_MODES and self._phase_code == PHASE_END

    @property
    def _standby(self) -> bool:
        """Stato di riposo, non la coda di un lavaggio appena terminato."""
        return self._cycle_over and not self.after_run

    @property
    def state(self) -> str:
        if not self.online:
            return STATE_OFF
        if self._cycle_over:
            if self.after_run:
                return STATE_FINISHED
            return STATE_REMOTE_READY if self.remote_control else STATE_IDLE
        return MACHINE_STATES.get(self.mode or 0, STATE_OFF)

    @property
    def running(self) -> bool:
        return self.mode in RUNNING_MODES and not self._cycle_over

    @property
    def phase(self) -> str | None:
        if not self.online:
            return None
        if self._standby:
            return PHASES[0]
        return PHASES.get(self._phase_code or 0)

    @property
    def remaining_minutes(self) -> int | None:
        if not self.online:
            return None
        rem = _int(self.raw, "RemTime")
        if self._cycle_over:
            return 0
        if rem is None:
            return None
        return round(rem / 60) if self.remtime_seconds else rem

    @property
    def program(self) -> int | None:
        return _int(self.raw, "Pr") if self.online else None

    @property
    def temperature(self) -> int | None:
        return _int(self.raw, "Temp") if self.online else None

    @property
    def spin_speed(self) -> int | None:
        spin = _int(self.raw, "SpinSp") if self.online else None
        return None if spin is None else spin * 100

    @property
    def remote_control(self) -> bool:
        return self.online and self.raw.get("WiFiStatus") == "1"

    @property
    def error(self) -> str:
        code = _int(self.raw, "Err") if self.online else None
        if not code:
            return "none"
        return ERROR_CODES.get(code, "unknown")

    @property
    def error_code(self) -> int | None:
        return _int(self.raw, "Err") if self.online else None


class SimplyFiCoordinator(DataUpdateCoordinator[WasherData]):
    """Interroga la lavatrice ogni 30 secondi.

    Non fallisce mai: una lavatrice spenta è uno stato normale ("off"), non
    un errore, così le entità restano disponibili e le automazioni scattano.
    """

    config_entry: SimplyFiConfigEntry

    def __init__(self, hass: HomeAssistant, entry: SimplyFiConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = SimplyFiClient(
            async_get_clientsession(hass),
            entry.data[CONF_HOST],
            entry.data.get(CONF_KEY),
        )
        self._remtime_seconds: bool = entry.data.get(CONF_REMTIME_SECONDS, False)
        self._failures = 0

    async def _async_update_data(self) -> WasherData:
        try:
            raw = await self.client.async_status()
        except SimplyFiError as err:
            self._failures += 1
            previous = self.data
            if (
                previous is not None
                and previous.online
                and self._failures < OFFLINE_AFTER_FAILURES
            ):
                _LOGGER.debug("Lettura fallita (%s), mantengo l'ultimo stato", err)
                return previous
            return WasherData(online=False, remtime_seconds=self._remtime_seconds)

        self._failures = 0
        data = WasherData(online=True, raw=raw, remtime_seconds=self._remtime_seconds)
        previous = self.data
        # Se la fase "Fine" arriva subito dopo un lavaggio in corso è la fine
        # vera del ciclo; altrimenti è solo la macchina a riposo.
        data.after_run = data._cycle_over and previous is not None and (
            previous.running or (previous._cycle_over and previous.after_run)
        )
        data.end_time = self._end_time(data)
        return data

    def _end_time(self, data: WasherData) -> datetime | None:
        """Ora di fine prevista, stabile finché la stima non cambia davvero."""
        remaining = data.remaining_minutes
        if not data.running or not remaining:
            return None
        estimate = dt_util.utcnow().replace(second=0, microsecond=0) + timedelta(
            minutes=remaining
        )
        previous = self.data.end_time if self.data else None
        if previous and abs(previous - estimate) <= END_TIME_TOLERANCE:
            return previous
        return estimate
