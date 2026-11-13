---
id: RPSW-20261113-001
date: 2026-11-13
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - hmi/deploy/xytheta-hmi-web.service
  - hmi/deploy/xytheta-hmi-kiosk.service
  - hmi/deploy/labwc-autostart
  - RPI4-HMI
tags:
  - raspberry-pi
  - touch-display-2
  - hmi
  - systemd
  - wayland
  - labwc
  - chromium
  - kiosk
  - deployment
related:
  - camera-inspection/touchscreen.md
---

# Deploy the UI-only HMI kiosk to the Raspberry Pi Touch Display 2

## Summary

RPI4-HMI now serves the committed browser HMI on loopback port 8766 and starts
it as a singleton Chromium kiosk on the 720×1280 portrait Touch Display 2. The
UI remains an explicitly marked demo/offline frontend with no machine-control
backend.

## Reason

The repository contained a navigable and tested HMI, but the Pi was only
holding the three static files. The previously attempted Python server could
not bind because the existing `xytheta-settings.service` already owned port
8765, and no kiosk was attached to the active Wayland session.

## Implementation

- Verified the installed `index.html`, `app.js`, and `styles.css` SHA-256 hashes
  against commit `a8ecec1`; no UI source change was required.
- Preserved `xytheta-settings.service` on `127.0.0.1:8765`. The HMI uses
  `127.0.0.1:8766` and opens `/?demo=1`.
- Added system service `xytheta-hmi-web.service` to run the static HTTP server
  as `rpi` with a read-only home, dropped privileges, and automatic restart.
- Added user service `xytheta-hmi-kiosk.service` to run Chromium in
  Wayland/kiosk mode at device scale 1, wait for the web service, and restart
  if Chromium exits.
- Replaced the labwc autostart's direct QML launch with a singleton kiosk
  restart. The prior file is preserved as
  `~/.config/labwc/autostart.before-xytheta-web-20261113`; all legacy QML
  files remain installed for manual fallback.
- Stopped the active legacy `qml6 /home/rpi/plotter-hmi/main.qml` process after
  the Chromium kiosk was active, removing the duplicate fullscreen UI.
- Added a dedicated ED25519 deployment key to `rpi`'s
  `~/.ssh/authorized_keys` for noninteractive verification. No password was
  stored in the repository, a service file, a script, or a committed artifact.
- Checked the deployment units and autostart definition into `hmi/deploy/` so
  the installed configuration can be reproduced.

## Verification

- `curl -sS -I http://127.0.0.1:8766/` returned `HTTP/1.0 200 OK`.
- `xytheta-hmi-web.service` and `xytheta-hmi-kiosk.service` were active at the
  same time; port 8765 remained owned by the unchanged settings API.
- The active DSI connector reported `720x1280` under Debian 13,
  Wayland/labwc 0.20.2, with Chromium 156. The kiosk held a Wayland connection
  and exposed the HMI page at `http://127.0.0.1:8766/?demo=1#/home`.
- The repository smoke test passed on the Windows Node.js 25.5.0 host. Pi
  Node.js was absent, so no Node package was installed on the Pi.
- Chromium DevTools touch input passed Home, Run, Camera, Jog, Tools, Optical
  registration, Inspect, Windows sync, Calibration profiles, nested Back paths,
  and cancel/confirm dialog handling.
- Every named screen measured exactly `720×1280` at scale 1 with
  `scrollWidth=720` and no visible button below 40 CSS pixels in either
  dimension. Visual captures were also inspected at the native viewport.

## Struggles and rejected approaches

- The original server command returned without an error but its background
  process died at bind time. The useful evidence was in
  `/tmp/xytheta-hmi.log`: `OSError: [Errno 98] Address already in use`.
- Moving or stopping `xytheta-settings.service` was rejected because it is an
  existing settings API and unrelated to the HMI.
- Launching Chromium directly from SSH was rejected because the kiosk must
  survive the initiating SSH session and remain singleton under systemd.
- The labwc graphical-session target is inactive, so a service ordered only
  against that target was not selected. The labwc autostart invokes the user
  service after the compositor and its Wayland environment exist.

## Risks and follow-up

- A cold reboot was not performed in this session. The autostart script and
  user-service start were exercised directly, but full boot persistence remains
  to be observed.
- Coordinate-level touch input reached the live Chromium page, but physical
  finger contact and multitouch mapping were not independently measured.
- The static UI server and kiosk are UI-only. Connecting sender, camera,
  inspection, or calibration services still requires the single-authority
  adapter and safety contract in `hmi/README.md`.
- Tailscale is not installed or active on RPI4-HMI. Preserve the loopback
  binding and use Tailscale Serve if tailnet access is added; do not expose
  Python directly on all interfaces.
- The active browser processes measured about 384 MiB proportional memory,
  while the whole 2 GB system used about 420 MiB and had about 1.4 GiB
  available. That leaves useful headroom now, but image workloads must be
  measured before assuming the same margin.
- The legacy QML application remains available but is no longer launched
  automatically. Deliberately starting it and the Chromium kiosk together would
  create two fullscreen HMIs.

## Files

- `hmi/deploy/xytheta-hmi-web.service`: reproducible static-server unit.
- `hmi/deploy/xytheta-hmi-kiosk.service`: reproducible Chromium user unit.
- `hmi/deploy/labwc-autostart`: graphical-session startup entry.
- `hmi/README.md`: current deployment, verification, and remaining acceptance
  state.
- `camera-inspection/touchscreen.md`,
  `camera-inspection/README.md`, and `camera-inspection/roadmap.md`: update the
  current HMI status and remaining backend work.
