# Changelog

All notable changes to this project are listed here. Versions follow
`MAJOR.MINOR.PATCH`; while the project is `0.x` it is experimental and any
release may contain breaking changes.

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
