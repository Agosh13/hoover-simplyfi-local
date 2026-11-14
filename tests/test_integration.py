"""Test dell'integrazione dentro un Home Assistant reale (di test)."""

from datetime import timedelta
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util

from custom_components.hoover_simplyfi.api import recover_key, xor
from custom_components.hoover_simplyfi.const import DOMAIN

HOST = "192.0.2.10"
KEY = "Abcdefgh12345678"
URL = f"http://{HOST}/http-read.json?encrypted=1"


def payload(**changes) -> str:
    """Risposta cifrata con lo stesso formato della lavatrice reale."""
    status = {
        "WiFiStatus": "0", "Err": "255", "MachMd": "2", "Pr": "2", "PrPh": "2",
        "SLevel": "255", "Temp": "60", "SpinSp": "12", "Opt1": "0",
        "Steam": "0", "DryT": "0", "DelVal": "255", "RemTime": "80",
        "RecipeId": "0", "CheckUpState": "0",
    }
    status.update(changes)
    fields = ",\r\n".join(f'\t\t"{k}":"{v}"' for k, v in status.items())
    body = '{\r\n\t"statusLavatrice":{\r\n' + fields + "\r\n\t}\r\n}"
    assert body.startswith('{\r\n\t"statusLavatrice":{')
    return xor(body.encode(), KEY).hex().upper()


@pytest.fixture(autouse=True)
def _custom(enable_custom_integrations, monkeypatch):
    monkeypatch.setattr("custom_components.hoover_simplyfi.api.RETRY_DELAY", 0)


def state(hass: HomeAssistant, entity_id: str) -> str:
    st = hass.states.get(entity_id)
    assert st is not None, f"{entity_id} mancante: {hass.states.async_entity_ids()}"
    return st.state


async def tick(hass: HomeAssistant, entry) -> None:
    """Esegue una lettura, come fa il coordinatore ogni 30 secondi."""
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


def test_recover_key() -> None:
    assert recover_key(bytes.fromhex(payload())) == KEY


async def test_config_flow(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, text=payload())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": HOST}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"host": HOST, "key": KEY, "remtime_in_seconds": False}
    assert result["options"] == {"model": "generic"}


async def test_config_flow_errors(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, exc=TimeoutError())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"host": HOST}
    )
    assert result["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text="<html>router</html>")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": HOST}
    )
    assert result["errors"] == {"base": "invalid_device"}


async def test_cycle_lifecycle(hass: HomeAssistant, aioclient_mock) -> None:
    """In funzione -> finito -> spenta, con una lettura persa in mezzo."""
    aioclient_mock.get(URL, text=payload())
    entry = MockConfigEntry(domain=DOMAIN, data={"host": HOST, "key": KEY})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert state(hass, "sensor.lavatrice_state") == "running"
    assert state(hass, "sensor.lavatrice_phase") == "wash"
    assert state(hass, "sensor.lavatrice_remaining_time") == "80"
    assert state(hass, "sensor.lavatrice_temperature") == "60"
    assert state(hass, "sensor.lavatrice_spin_speed") == "1200"
    assert state(hass, "sensor.lavatrice_error") == "none"
    assert state(hass, "binary_sensor.lavatrice_cycle_running") == "on"
    end = dt_util.parse_datetime(state(hass, "sensor.lavatrice_estimated_end"))
    assert timedelta(minutes=78) < end - dt_util.utcnow() < timedelta(minutes=81)

    # Una lettura persa non deve far sembrare finito il lavaggio.
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, exc=TimeoutError())
    await tick(hass, entry)
    assert state(hass, "binary_sensor.lavatrice_cycle_running") == "on"

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text=payload(MachMd="7", PrPh="5", RemTime="0"))
    await tick(hass, entry)
    assert state(hass, "sensor.lavatrice_state") == "finished"
    assert state(hass, "binary_sensor.lavatrice_cycle_running") == "off"
    assert state(hass, "sensor.lavatrice_estimated_end") == "unknown"

    # Spenta a lungo: stato "off", entità ancora disponibili.
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, exc=TimeoutError())
    for _ in range(5):
        await tick(hass, entry)
    assert state(hass, "sensor.lavatrice_state") == "off"
    assert state(hass, "binary_sensor.lavatrice_cycle_running") == "off"


async def test_setup_while_washer_off(hass: HomeAssistant, aioclient_mock) -> None:
    """Riavvio di Home Assistant con la lavatrice spenta: nessun errore."""
    aioclient_mock.get(URL, exc=TimeoutError())
    entry = MockConfigEntry(domain=DOMAIN, data={"host": HOST, "key": KEY})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert state(hass, "sensor.lavatrice_state") == "off"

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text=payload(MachMd="1", PrPh="0", RemTime="0"))
    await tick(hass, entry)
    assert state(hass, "sensor.lavatrice_state") == "idle"


async def test_power_cycle_after_end_is_not_a_new_cycle(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Caso reale: riaccesa a ciclo finito, la macchina dice di nuovo "in funzione".

    Riporta MachMd=2 con la fase ferma su Fine e un tempo rimanente fasullo.
    Non deve risultare un lavaggio in corso, altrimenti quando poi torna ferma
    parte una seconda notifica di fine lavaggio.
    """
    aioclient_mock.get(URL, text=payload(MachMd="2", PrPh="3", RemTime="3"))
    entry = MockConfigEntry(domain=DOMAIN, data={"host": HOST, "key": KEY})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert state(hass, "binary_sensor.lavatrice_cycle_running") == "on"

    changes: list[str] = []
    hass.bus.async_listen(
        "state_changed",
        lambda e: changes.append(e.data["new_state"].state)
        if e.data["entity_id"] == "binary_sensor.lavatrice_cycle_running"
        else None,
    )

    for fields in (
        {"MachMd": "7", "PrPh": "5", "RemTime": "0"},  # fine reale
        {"MachMd": "2", "PrPh": "5", "RemTime": "310"},  # riaccesa: falso "in funzione"
        {"MachMd": "1", "PrPh": "0", "RemTime": "131", "Pr": "15"},  # ferma
    ):
        aioclient_mock.clear_requests()
        aioclient_mock.get(URL, text=payload(**fields))
        await tick(hass, entry)
        if fields["RemTime"] == "310":
            assert state(hass, "sensor.lavatrice_state") == "idle"
            assert state(hass, "sensor.lavatrice_remaining_time") == "0"

    assert changes == ["off"], "una sola fine lavaggio"
    assert state(hass, "sensor.lavatrice_state") == "idle"


async def test_program_name_follows_model_option(
    hass: HomeAssistant, aioclient_mock
) -> None:
    aioclient_mock.get(URL, text=payload(Pr="13"))
    entry = MockConfigEntry(domain=DOMAIN, data={"host": HOST, "key": KEY})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.lavatrice_program_name") is None
    assert state(hass, "sensor.lavatrice_program_position") == "13"

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"model": "hoover_link_pro"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert state(hass, "sensor.lavatrice_program_name") == "eco_40_60"

    # Posizione nascosta, senza nome noto.
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text=payload(Pr="17"))
    await tick(hass, entry)
    assert state(hass, "sensor.lavatrice_program_name") == "unknown"


async def test_remote_ready_and_real_end_through_end_phase(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """MachMd=2 con fase Fine: attesa comando remoto, oppure fine vera se segue un lavaggio."""
    armed = {"MachMd": "2", "PrPh": "5", "RemTime": "310", "Pr": "15", "WiFiStatus": "1"}
    aioclient_mock.get(URL, text=payload(**armed))
    entry = MockConfigEntry(domain=DOMAIN, data={"host": HOST, "key": KEY})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert state(hass, "sensor.lavatrice_state") == "remote_ready"
    assert state(hass, "sensor.lavatrice_phase") == "stopped"
    assert state(hass, "binary_sensor.lavatrice_cycle_running") == "off"

    # L'app avvia un ciclo...
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text=payload(MachMd="2", PrPh="2", RemTime="96", WiFiStatus="1"))
    await tick(hass, entry)
    assert state(hass, "sensor.lavatrice_state") == "running"

    # ...che termina passando per "in funzione + fase Fine": è una fine vera,
    # e resta tale alle letture successive.
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text=payload(**armed))
    for _ in range(2):
        await tick(hass, entry)
        assert state(hass, "sensor.lavatrice_state") == "finished"
        assert state(hass, "sensor.lavatrice_phase") == "end"
