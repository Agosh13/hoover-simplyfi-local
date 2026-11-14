# Hoover/Candy simply-Fi — local integration for Home Assistant

> [!WARNING]
> **Experimental — alpha.** This project is at a very early stage. It has been
> tested on a single washing machine, for a short time. Expect bugs, breaking
> changes between versions, and entities that may be renamed. Read the
> [disclaimer](#disclaimer) before installing.

Read the status of a Hoover or Candy **simply-Fi** washing machine straight from
your local network: no cloud, no account, no phone app.

## Why this exists

The official apps for the simply-Fi platform (*Hoover Wizard*, *Candy simply-Fi*)
are no longer maintained and stop working on recent phones. The washing machine
itself is fine: its Wi-Fi module still answers on the local network, it just has
nothing left to talk to.

The goal of this project is deliberately small:

- **know when the wash is finished**, and get a notification;
- see what the machine is doing (state, phase, time left);
- depend on nothing outside your home: no vendor cloud, no app, no computer
  left switched on. It runs inside Home Assistant.

It is **read-only**. It does not start, stop or change cycles.

## What you get

| Entity | Meaning |
|---|---|
| Cycle running | on while a cycle is running or paused — the one to use for "finished" notifications |
| State | off, idle, waiting for remote command, running, paused, delayed start, error, finished |
| Phase | pre-wash, wash, rinse, spin, … |
| Remaining time | minutes until the end of the cycle |
| Estimated end | clock time at which the cycle should end |
| Program name | name of the selected program (models with a known dial, see [Program names](#program-names)) |
| Program position | position of the program dial |
| Temperature, Spin speed | settings of the current cycle |
| Error, Remote control | diagnostics |

Entity names are translated in English and Italian.

## Compatibility

- **Works with:** washing machines on the older *simply-Fi* platform (Hoover
  Wizard / Candy simply-Fi apps).
- **Tested on:** Hoover `HLPS139TAMBE-11`. That is the only confirmed model.
- **Does not work with:** appliances on the newer **hOn** platform, which is
  cloud-only.
- Dryers, dishwashers, ovens and other simply-Fi appliances use the same
  protocol but are **not supported yet**.
- Requires Home Assistant 2025.4 or newer.

## Installation

### HACS (recommended)

1. HACS → ⋮ menu → **Custom repositories**.
2. Add `https://github.com/Agosh13/hoover-simplyfi-local` with type **Integration**.
3. Search for "Hoover/Candy simply-Fi" in HACS, download it, restart Home Assistant.

### Manual

Copy `custom_components/hoover_simplyfi` into your Home Assistant
`config/custom_components/` folder and restart.

## Setup

1. Switch the washing machine **on**.
2. Settings → Devices & services → **Add integration** → "Hoover/Candy simply-Fi".
3. Enter the washing machine's IP address and pick your **model**, if listed.

That is all: the encryption key is recovered automatically. Give the machine a
fixed IP address (a DHCP reservation on your router), otherwise the integration
loses it when the address changes.

## Notify me when the wash is done

```yaml
automation:
  - alias: Washing machine finished
    triggers:
      - trigger: state
        entity_id: binary_sensor.lavatrice_cycle_running
        from: "on"
        to: "off"
    actions:
      - action: notify.notify
        data:
          title: Washing machine
          message: The wash is done.
```

Check the exact entity id in your installation (it depends on your language),
and replace `notify.notify` with your phone's notify service, for example
`notify.mobile_app_my_iphone`.

The example above fires whenever a cycle stops being in progress, including
when you switch the machine off halfway through. If you only want a message for
cycles that really reached the end, trigger on the state instead:

```yaml
    triggers:
      - trigger: state
        entity_id: sensor.lavatrice_state
        to: finished
```

## Program names

The machine only reports the **position** of the program dial. To show a name,
the integration needs to know the dial of your model. Choose the model during
setup, or later from the integration's **Configure** button.

| Model | Status |
|---|---|
| Hoover LINK PRO (`HLPS…TAMBE`) | 15 positions verified on `HLPS139TAMBE-11` |
| Anything else | choose *Generic*: you get the dial position only |

Hoover LINK PRO dial: 1 20 °C · 2 Hygiene 60 °C · 3 Coloured 59' · 4 Rapid
14'/30'/44' · 5 Delicates · 6 Wool · 7 Hand wash & Silk · 8 Rinse · 9 Drain &
Spin · 10 Shirts · 11 Hygiene PRO 59' · 12 Mixed · 13 ECO 40-60 · 14 Cotton ·
15 Auto-Hygiene (the position reported while the dial is on remote control).

Want your model added? Open an issue with the model number and the list of
programs in dial order.

## FAQ

**How do I find the washing machine's IP address?**
Look at the device list of your router. The Wi-Fi module usually shows up with a
generic name such as `espXXXXXX` or `ESP_XXXXXX`, not as "Hoover". If you have
several, the right one is the one that answers at
`http://<ip>/http-read.json?encrypted=1` with a long string of letters and digits.

**My router has two Wi-Fi networks (2.4 GHz and 5 GHz). Is that a problem?**
No, as long as both belong to the same home network. The washing machine only
connects to **2.4 GHz**; Home Assistant can be on 5 GHz or on a cable. What
matters is that Home Assistant can reach the machine's IP address. It will *not*
work if the machine sits on an isolated guest network, or on a separate IoT
network/VLAN with no route from Home Assistant.

**The official app no longer works. Can I still connect the machine to Wi-Fi?**
If the machine was already paired with your Wi-Fi, it stays connected and this
integration works. Pairing a machine to a *new* Wi-Fi network normally needs the
official app, and this integration cannot do it (yet). If you change router,
keeping the same network name and password avoids the problem.

**Do I need a Hoover/Candy account, or the internet?**
No. Everything happens between Home Assistant and the machine on your network.

**The state says "Off" although the machine is plugged in.**
When the machine is switched off at its panel, its Wi-Fi module stops answering.
That is reported as **Off**, and the entities stay available. As soon as you
switch it on, the state updates within about 30 seconds.

**I switched the machine off and on after a wash and got a second "finished" notification.**
Fixed in `0.2.0`. Some machines have a resting state in which they claim to be
running while the phase is "End": it shows up when the machine is switched back
on after a finished cycle, and while it waits for a command from the app. It is
no longer treated as a cycle in progress. Since `0.3.0` it is shown as *Idle*
or *Waiting for remote command* rather than *Finished*.

**Will a Wi-Fi hiccup trigger a false "finished" notification?**
It should not: a few missed readings are ignored and the last known state is
kept. Only after about two minutes of silence the machine is considered off.

**The remaining time is absurdly large.**
Some firmware reports the remaining time in seconds instead of minutes. Remove
the integration and add it again, ticking *Remaining time is reported in
seconds*.

**Readings fail when I also use another tool or script.**
The machine's Wi-Fi module handles **one connection at a time**. If something
else queries it at the same moment (another script, another integration, a
browser tab), requests time out. Let Home Assistant be the only one talking to it.

**Can I start or stop a cycle from Home Assistant?**
Not in this version. The protocol allows it (with the machine in remote-control
mode), but commands are out of scope for the alpha: reading the status is safe,
starting a physical machine by mistake is not.

**Is the connection secure?**
No more than the machine itself. The local protocol has no authentication, and
its "encryption" is a simple XOR whose key can be recovered from a single reply
— which is exactly how this integration sets itself up. Anyone on your home
network can read the machine's status, with or without this project. Do not
expose the machine to the internet.

**Is my model supported?**
If it used the Hoover Wizard or Candy simply-Fi app, probably. Try it and open an
issue with the model number and what you see, working or not.

## Versions

Versions follow `MAJOR.MINOR.PATCH` and are published as tags and GitHub
releases; HACS offers them as updates. While the project is `0.x` it stays
experimental and any release may contain breaking changes. See the
[changelog](CHANGELOG.md).

## Known limitations

- Alpha: one tested model, a few hours of real use.
- The end of a real cycle has been verified only in automated tests with
  simulated data; behaviour at the end of a cycle may differ between models.
- Read-only. No statistics, no options, no commands.
- Program names are known for one model family only.
- Polls every 30 seconds, so changes show up with that delay.

## Disclaimer

This is an independent, unofficial hobby project. It is **not affiliated with,
endorsed by, or supported by** Hoover, Candy, Haier or any of their companies.
All product and brand names belong to their respective owners.

The integration relies on an undocumented local interface that was worked out by
the community. It may stop working at any time, for example after a firmware
update.

The software is provided **"as is", without warranty of any kind**. You use it
entirely at your own risk. The authors accept no responsibility for damage to
appliances, property or data, for missed or wrong notifications, or for any
other consequence of its use. Do not rely on it for anything safety-related: it
is a convenience, not a monitoring or safety system. A washing machine is a
water- and mains-connected appliance — do not leave it unattended on the basis
of what this integration reports.

## Protocol notes

What was learned about the local protocol on the tested machine — status
quirks, the program table, and the commands the official app sends — is in
[docs/protocol-notes.md](docs/protocol-notes.md).

## Credits

The local protocol was documented by the community, in particular
[dandwhelan/candy-hoover-local](https://github.com/dandwhelan/candy-hoover-local),
[ofalvai/home-assistant-candy](https://github.com/ofalvai/home-assistant-candy)
and the
[Home Assistant Community thread on Candy simply-Fi](https://community.home-assistant.io/t/dishwasher-candy-simply-fi-cdi-6015-wifi/136543).

## License

[MIT](LICENSE)
