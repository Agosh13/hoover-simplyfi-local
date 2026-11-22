# Protocol notes — Hoover LINK PRO (`HLPS139TAMBE-11`)

Field notes from one real machine. They complement the general description of
the simply-Fi local API in
[dandwhelan/candy-hoover-local](https://github.com/dandwhelan/candy-hoover-local/blob/main/PROTOCOL.md);
only what differs from it, or was confirmed on this model, is listed here.

The integration is read-only unless commands are enabled in its options. When
they are, it sends exactly the commands below: the program selection, and the
start and stop observed from the official app.

## Transport

- `GET /http-read.json?encrypted=1` works; `encrypted=0` answers
  `{"response":"BAD REQUEST"}`. Replies are always XOR-encrypted, hex, uppercase.
- The status document starts with `{\r\n\t"statusLavatrice":{`, so the 16-byte
  key can be recovered from the first reply. An error reply is
  `{"response":"ERROR"}`.
- The Wi-Fi module serves **one connection at a time**. Concurrent clients make
  requests hang until they time out.
- `http-getStatistics.json` (with or without `http-prepareStatistics.json`
  first) answers `ERROR` on this firmware.

## Status fields

| Field | Notes |
|---|---|
| `RemTime` | **minutes** on this model (drops by 1 per minute), not seconds |
| `PrCode` | not present |
| `Pr` | dial position; `15` while the dial is on the remote-control position |
| `WiFiStatus` | `1` only when the dial is on the remote-control position |
| `SpinSp` | rpm ÷ 100 |
| `SLevel` | soil level 1–3, `255` when the program has none |

### `MachMd` = 2 does not always mean "running"

`MachMd=2` together with `PrPh=5` (End) and `RemTime=310` is a **resting
state**, not a cycle:

- it is what the machine reports while waiting for a command from the app
  (dial on remote control, `Pr=15`, `WiFiStatus=1`);
- it also appears after switching the machine off and on once a cycle has
  finished (`WiFiStatus=0`, `Pr` still on the last program).

A real end of cycle was observed as `MachMd=7`, `PrPh=5`.

## Programs

Selecting a position **without starting** it:

```
Write=1&StSt=0&PrNm=<position>&DelVl=0
```

The machine answers `SUCCESS` and the next status shows that program's default
temperature, spin, soil level and duration, with `MachMd=1`. This is how the
table below was read, and it matches the program table in the user manual.

| Pos. | Program | Temp | Spin | Minutes |
|---|---|---|---|---|
| 1 | 20 °C | 20 | 1200 | 126 |
| 2 | Hygiene 60 °C | 60 | 1200 | 96 |
| 3 | Coloured 59' | 40 | 800 | 59 |
| 4 | Rapid 14'/30'/44' | 30 | 800 | 14 |
| 5 | Delicates | 30 | 400 | 59 |
| 6 | Wool | 30 | 800 | 49 |
| 7 | Hand wash & Silk | 30 | 800 | 49 |
| 8 | Rinse | – | 1200 | 29 |
| 9 | Drain & Spin | – | 1200 | 10 |
| 10 | Shirts | 30 | 1200 | 77 |
| 11 | Hygiene PRO 59' | 60 | 800 | 59 |
| 12 | Mixed | 40 | 1200 | 117 |
| 13 | ECO 40-60 | – | 1300 | 185 |
| 14 | Cotton | 40 | 1300 | 170 |
| 15 | Auto-Hygiene (remote-control position) | 90 | 400 | 131 |

Positions 16–20 are also accepted but are not on the dial and their names are
unknown (probably app-only programs): 16 → 1 min, no spin; 17 → 30 °C, no spin,
46 min; 18 → 40 °C, 800 rpm, 59 min; 19 and 20 → 169 min, no spin.

## What the official app sends

Captured from the iOS app (`hoover-ios/3.9.0`). The app sends the `data`
parameter as **lowercase** hex and keeps the connection alive.

**Stop** button, pressed while the machine was in the resting state described
above (which the app shows as a cycle in progress):

```
Write=1&StSt=0&DelMd=0&PrNm=15
```

It was pressed on an idle machine, and it was also used on a delayed start
(see below), where it cancelled the countdown: the display cleared. Its effect
on a running wash is still unverified.

Start of program 2 with the spin lowered from the default 1200 to 900 rpm,
temperature left at its default:

```
Write=1&Pa=0&Sel=0&PrNm=2&StSt=1&SpdTgt=9&SpdDef=12&Stm=0&RecipeId=0&CheckUpState=0
```

So on this model the start command carries the dial position only: no `PrCode`,
no `PrStr`, no option mask. The temperature parameter is omitted when unchanged.

This matches the app's command builder as described in the developer notes of
the [openHAB Candy binding](https://github.com/openhab/openhab-addons/tree/main/bundles/org.openhab.binding.candy):
the prefix is `Write=1&Pa=0&Sel=0&PrNm=<position>`, and each override is
emitted together with its default only when it differs from it — `SpdTgt` with
`SpdDef` for the spin, `TmpTgt` with `TmpDf` for the temperature (the latter
not yet observed on this machine).

### Delayed start (observed)

Setting a delayed start **does not start the machine**. The app sent:

```
Write=1&Pa=0&Sel=0&PrNm=8&DelMd=1&DelVl=2&SpdTgt=10&SpdDef=12&Stm=0&RecipeId=0&CheckUpState=0
```

with no `StSt=1`. Afterwards the status read `MachMd=5` (delayed start),
`DelVal=2`, `Pr=8`, and the display showed a countdown. The delay survived
closing and reopening the app.

- `DelVl` is in **hours** on this model: the app showed "2 ore" and the status
  reports `DelVal=2`. The documentation says 30-minute steps, which does not
  match here.
- The delay is in whole hours from 1 to 24 (the Hoover `HBDOS695TAMCE-80` notes
  in [Holdness/hoover-washer-local](https://github.com/Holdness/hoover-washer-local/blob/main/docs/protocol.md)
  say the same, for another model of the same family).
- The app's **Stop** cancelled the countdown: `Write=1&StSt=0&DelMd=0&PrNm=8`,
  with no `DelVl=0`. Confirmed on the display, not by a status read after it.
- Not observed on this model: whether the machine starts on its own when a
  countdown reaches zero. The notes above say it does, on another model, and
  that the washer's Wi-Fi web server then stops answering until the washer is
  power-cycled. Not tested here.
- In an earlier test with program 14 the status read after reopening the app
  showed no delay (`DelVal=255`, `Pr=15`), even though the same `DelMd=1&DelVl=2`
  had been sent. Unexplained.

Other community sources (Android app, other models) use a different start
command with `PrCode`, `PrStr` and `OptMsk1/2`, and stop a running cycle with
`Write=1&StSt=0&PrNm=<running position>&DelVl=0`.

On this model the app offers **stop** but no pause.

Not captured yet: stop during a running wash, a changed temperature, options,
and whether a delayed start begins on its own when the countdown ends.

## Community notes (other models)

From [Holdness/hoover-washer-local](https://github.com/Holdness/hoover-washer-local/blob/main/docs/protocol.md),
a Hoover `HBDOS695TAMCE-80` (same family, different model). Not verified on the
LINK PRO:

- Spin above the programme default left that washer beeping and off the network
  until it was power-cycled. Lower speeds worked. The integration sends a spin
  only when lower than the default.
- About five minutes after going idle the washer sleeps, reports a misleading
  "running" status and refuses commands with `READ ONLY`; turning the dial off
  and back on wakes it.
- The washer's own status shows the dial position during a delay, not the
  programme that was sent.
