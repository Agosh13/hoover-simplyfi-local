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

It was not sent during a real cycle, so its effect on a running wash is
unverified.

Start of program 2 with the spin lowered from the default 1200 to 900 rpm,
temperature left at its default:

```
Write=1&Pa=0&Sel=0&PrNm=2&StSt=1&SpdTgt=9&SpdDef=12&Stm=0&RecipeId=0&CheckUpState=0
```

So on this model the start command carries the dial position only: no `PrCode`,
no `PrStr`, no option mask. The temperature parameter is omitted when unchanged.

On this model the app offers **stop** but no pause.

Not captured yet: stop during a real cycle, a changed temperature, options,
delayed start.
