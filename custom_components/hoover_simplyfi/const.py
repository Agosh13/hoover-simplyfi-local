"""Costanti dell'integrazione Hoover/Candy simply-Fi locale."""

from datetime import timedelta

DOMAIN = "hoover_simplyfi"

CONF_KEY = "key"
CONF_REMTIME_SECONDS = "remtime_in_seconds"
CONF_MODEL = "model"

MODEL_GENERIC = "generic"

# Nome del programma per ogni posizione della manopola, per modello.
# La posizione è il campo `Pr` dello stato. Si aggiungono solo le posizioni
# verificate: quelle sconosciute restano senza nome.
PROGRAM_SETS: dict[str, dict[int, str]] = {
    # Hoover LINK PRO (HLPS...TAMBE). Verificato su HLPS139TAMBE-11 selezionando
    # ogni posizione da remoto e confrontando i valori con la tabella del manuale.
    "hoover_link_pro": {
        1: "all_in_one_20",
        2: "hygiene_60",
        3: "coloured_59",
        4: "rapid",
        5: "delicates",
        6: "wool",
        7: "hand_wash_silk",
        8: "rinse",
        9: "drain_spin",
        10: "shirts",
        11: "hygiene_pro_59",
        12: "mixed",
        13: "eco_40_60",
        14: "cotton",
        15: "auto_hygiene",
    },
}

SCAN_INTERVAL = timedelta(seconds=30)

# Letture fallite consecutive prima di considerare la lavatrice spenta.
# Il modulo Wi-Fi ogni tanto non risponde: una lettura persa non deve far
# sembrare finito il lavaggio.
OFFLINE_AFTER_FAILURES = 4

STATE_OFF = "off"
STATE_FINISHED = "finished"
STATE_IDLE = "idle"
STATE_REMOTE_READY = "remote_ready"
MACHINE_STATES = {
    1: "idle",
    2: "running",
    3: "paused",
    4: "delayed_start_selected",
    5: "delayed_start",
    6: "error",
    7: "finished",
    8: "finished",
}
RUNNING_MODES = (2, 3)
PHASE_END = 5

PHASES = {
    0: "stopped",
    1: "prewash",
    2: "wash",
    3: "rinse",
    4: "last_rinse",
    5: "end",
    6: "drying",
    7: "error",
    8: "steam",
    9: "good_night",
    10: "spin",
}

ERROR_CODES = {
    1: "door_lock",
    7: "door_lock",
    2: "water_inlet",
    3: "drain",
    4: "water_level",
    6: "unbalanced",
    8: "drum_rotation",
    12: "drying",
    16: "heating",
    5: "electronics",
    9: "electronics",
    11: "electronics",
    13: "electronics",
    15: "electronics",
    17: "electronics",
}
