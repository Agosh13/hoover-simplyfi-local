"""Costanti dell'integrazione Hoover/Candy simply-Fi locale."""

from datetime import timedelta

DOMAIN = "hoover_simplyfi"

CONF_KEY = "key"
CONF_REMTIME_SECONDS = "remtime_in_seconds"

SCAN_INTERVAL = timedelta(seconds=30)

# Letture fallite consecutive prima di considerare la lavatrice spenta.
# Il modulo Wi-Fi ogni tanto non risponde: una lettura persa non deve far
# sembrare finito il lavaggio.
OFFLINE_AFTER_FAILURES = 4

STATE_OFF = "off"
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
