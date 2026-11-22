# Changelog

All notable changes to this project are listed here. Versions follow
`MAJOR.MINOR.PATCH`; while the project is `0.x` it is experimental and any
release may contain breaking changes.

## 0.4.2 — 2026-11-22

### Added

- **Start delay** (experimental, with commands enabled): a *Start delay* entity
  in whole hours, 0 to 24. With a delay the start command is
  `DelMd=1&DelVl=<hours>` and no `StSt=1`, as the official app sends it; the
  washer holds the countdown and starts by itself. Checked on the Hoover
  LINK PRO: the countdown appeared and the Stop of the app cancelled it.
  Whether the wash then starts on its own is not yet verified.

## 0.4.1 — 2026-11-14

### Changed

- The start command now carries the spin speed only when it differs from the
  program's default, as the official app does, and never for programs without
  a spin. Checked against the app's command builder as documented by the
  openHAB Candy binding.
- The reply to a command is accepted regardless of letter case (`SUCCESS` /
  `success`).

## 0.4.0 — 2026-11-14

### Added

- **Commands (experimental, off by default).** Enable them from the
  integration's Configure dialog; a listed model is required. New entities:
  *Program to start* (selects the program without starting it), *Spin speed to
  start*, *Start* and *Stop*. They work only with the dial on the
  remote-control position.
- Reads and commands are serialised, since the Wi-Fi module serves one
  connection at a time.

### Notes

- Start always uses the program's default temperature; options and delayed
  start are not supported.
- Stop sends the command captured from the official app, which was not
  verified during a real cycle.
- Protocol notes: the first captured app command is the app's Stop button, not
  a selection reset.

## 0.3.0 — 2026-11-14

### Changed
- The resting state in which the machine claims to be running while the phase
  is "End" is no longer shown as *Finished*. It is now *Waiting for remote
  command* when the dial is on remote control, and *Idle* otherwise. A cycle
  that really ends is still reported as *Finished*, including when it ends by
  passing through that state.
- In that resting state the phase is shown as *Stopped*.

### Added
- New state **Waiting for remote command**.
- [Protocol notes](docs/protocol-notes.md) for the Hoover LINK PRO: status
  quirks, program table, and the start command sent by the official app.

### Upgrade notes
- Automations that trigger on the state becoming `finished` keep working. If
  you relied on `finished` being shown while the machine was merely waiting on
  the remote-control position, use `remote_ready` instead.

## 0.2.0 — 2026-11-14

### Fixed
- False "wash finished" notification after switching the machine off and on
  again. A machine switched back on after a finished cycle reports itself as
  running while the phase is still "End"; this is now treated as finished, not
  as a new cycle.

### Added
- **Program name** sensor, shown once a model is selected (during setup or from
  the integration's *Configure* button).
- Hoover LINK PRO (`HLPS…TAMBE`) dial: 15 positions, verified on
  `HLPS139TAMBE-11`.

### Changed
- The "Program" sensor is now called "Program position". Its entity id does not
  change on existing installations.

## 0.1.0 — 2026-11-14

First alpha.

- Local, read-only status of Hoover/Candy simply-Fi washing machines.
- Setup from the UI with the IP address only; the encryption key is recovered
  automatically.
- Sensors: cycle running, state, phase, remaining time, estimated end, program
  position, temperature, spin speed, error, remote control.
- A switched-off machine is reported as "Off" instead of unavailable, and a few
  missed readings are ignored.
