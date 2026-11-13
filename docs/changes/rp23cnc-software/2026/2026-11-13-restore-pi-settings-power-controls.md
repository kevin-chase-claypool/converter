---
id: RPSW-20261113-003
date: 2026-11-13
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - hmi/app.js
  - hmi/index.html
  - hmi/styles.css
  - hmi/pi/xytheta-settings-service.py
  - hmi/deploy/xytheta-settings.service
tags:
  - touchscreen
  - hmi
  - display-brightness
  - inactivity-timeout
  - system-power
  - restart
  - poweroff
  - systemd
  - safety
related:
  - RPSW-20261113-001
  - RPSW-20261113-002
---

# Restore Pi display settings and add confirmed power controls

## Summary

The browser HMI now has **Tools → Pi settings & power**, restoring real display
brightness and inactivity timeout controls. It also provides separately
confirmed Restart Pi and Power off Pi actions. Wi-Fi state is visible read-only
until the touchscreen has a reliable browser keyboard.

## Reason

The browser replacement omitted the old QML Settings pages even though the
loopback settings service still owned the functionality. Brightness remained at
its stored raw value 19/31, and the five-minute timeout remained stored, but the
operator could not change either from the new HMI. No reboot or power-off
control existed.

## Implementation

- Added a hierarchical Pi settings screen with a native-range brightness
  control, 25/50/75/100% shortcuts, inactivity choices, network status,
  Restart Pi, and Power off Pi.
- Restored a touch-to-resume inactivity overlay driven by the stored timeout.
- Source-controlled the settings API under `hmi/pi/` and installed it from that
  location through `hmi/deploy/xytheta-settings.service`.
- Retained loopback-only binding on `127.0.0.1:8765`.
- Added origin checks for mutating requests. The local HMI origins are
  `http://127.0.0.1:8766` and `http://localhost:8766`; other browser origins
  receive HTTP 403 before a mutation is processed.
- `POST /reboot` requires `confirm=RESTART`; `POST /poweroff` requires
  `confirm=POWER OFF`. A second in-flight system action is rejected.
- Both destructive UI actions require an alert dialog whose confirmation button
  names the action. Valid requests are handed to
  `systemctl --no-block reboot|poweroff`.
- Wi-Fi scan/connect remains intentionally absent from the browser UI because
  Chromium currently lacks a dependable on-screen keyboard for passwords.

## Verification

- `node hmi/tests/smoke.cjs` passes for 17 views, global transport controls,
  Pi-settings rendering, and restart-dialog cancellation.
- `node --check hmi/app.js`, Python bytecode compilation, and scoped
  `git diff --check` pass.
- The active settings API reports brightness `19/31`, timeout `5` minutes,
  Wi-Fi interface `wlan0`, and infrastructure mode.
- A same-value brightness write and the existing timeout value were accepted,
  proving those mutation paths without changing the operator's current setup.
- The local-origin preflight returned 200. A foreign-origin preflight returned
  403. A reboot POST with the wrong confirmation returned 400 and did not
  invoke systemctl; the power-off endpoint also rejected a test request without
  the `POWER OFF` confirmation.
- The timeout was temporarily set to one minute and the stored five-minute
  value restored afterward. A 65-second Chromium virtual-time render displayed
  the touch-to-resume overlay, confirming that the timer follows the stored
  setting.
- A native 720×1280 Pi-settings screenshot was inspected. The page shows the
  loaded brightness, timeout, network, and power controls with the persistent
  transport strip.

The valid reboot and power-off commands were deliberately **not** executed.
Their final systemctl path remains a maintenance-window test rather than a
claimed completed shutdown.

## Struggles and rejected approaches

- Exposing Python directly on the LAN was rejected. Keep the root service on
  loopback and use a separately authenticated proxy if remote settings are
  needed.
- Keeping `Access-Control-Allow-Origin: *` was rejected for a root service that
  can now power off the host.
- A simple button click without backend confirmation was rejected. Both the UI
  dialog and endpoint payload require deliberate confirmation.
- Restoring Wi-Fi password entry before an on-screen keyboard exists was
  rejected because it would produce an unusable touch workflow.

## Risks and follow-up

- The valid restart/power-off systemctl path remains untested until an approved
  maintenance window. The operator must expect the HMI and SSH connection to
  disappear immediately.
- Powering off the Pi does not itself prove the plotter is idle or the pen is
  parked. Future motion integration must supply an authoritative supervisor
  interlock before enabling these controls during an actual job.
- Wi-Fi connection changes still require either a reliable browser/OSK path or
  temporary command-line access.
- Do not expose port 8765 publicly or through Tailscale Funnel. Remote settings
  require an authenticated same-origin proxy.

## Files

- `hmi/app.js`, `hmi/index.html`, and `hmi/styles.css`: Pi settings hierarchy,
  real display controls, idle overlay, and confirmed system actions.
- `hmi/tests/smoke.cjs`: 17-view and settings/power-dialog coverage.
- `hmi/pi/xytheta-settings-service.py`: allowlisted local API with origin and
  confirmation checks.
- `hmi/deploy/xytheta-settings.service`: installed service definition.
- `docs/integration/INTERFACES.md`: records the loopback settings and
  destructive confirmation contract.
- `hmi/README.md` and `camera-inspection/touchscreen.md`: current control,
  security, and acceptance state.
