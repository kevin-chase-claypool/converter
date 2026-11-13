# XY-Theta Touch Display 2 HMI — navigable frontend

**Status: browser UI deployed to RPI4-HMI; no machine backend yet.** The
frontend runs in a Chromium kiosk on the Raspberry Pi Touch Display 2. There is
**no live sender, motion supervisor, ESP32-P4 image service, calibration store,
or Windows synchronization API** connected to these screens yet. The frontend
deliberately never sends motor commands, G-code, machine macros, or synthetic
calibration approvals.

## Launch on the Pi (or a desktop for review)

Run from the repository root:

    cd hmi
    python3 -m http.server 8080 --bind 127.0.0.1

Open **http://127.0.0.1:8080/** in Chromium. For a dedicated Pi kiosk, open the URL with Chromium's --kiosk flag once screen orientation, touch mapping, startup, screen blanking, and display scaling have been verified. The interface targets the official **720×1280 portrait Touch Display 2**, is responsive to smaller browser windows, and uses no external JavaScript/CSS libraries.

**Interactive demo:** open **http://127.0.0.1:8080/?demo=1** or use **Home → System status → Try interactive demo**. Every screen is marked **SIMULATION** and every motion-related interaction changes *only* local mock state. Demo exists to exercise navigation, confirmation dialogs, lockouts and scan/sync progress before backend integration. No demo state is a measurement, captured image or successful hardware command. Without demo mode, the screen says **OFFLINE** and all hardware actions are unavailable.

## Deployed RPI4-HMI configuration

The machine-side deployment on 2026-11-13 uses:

- Debian 13 (Trixie) on a Raspberry Pi 4, Raspberry Pi Touch Display 2 at the
  active DSI mode **720×1280**, Wayland/labwc, and Chromium 156.
- `/home/rpi/xytheta-hmi/` for the three static UI files, matching commit
  `a8ecec1`.
- Loopback URL **http://127.0.0.1:8766/?demo=1**. The existing
  `xytheta-settings.service` owns port 8765 for Wi-Fi, brightness, and timeout
  settings, so it was left unchanged.
- System service `xytheta-hmi-web.service` for the static Python HTTP server,
  and user service `xytheta-hmi-kiosk.service` for Chromium.
- `~/.config/labwc/autostart` to restart the singleton kiosk service after
  labwc starts. The prior QML autostart file is backed up beside it as
  `autostart.before-xytheta-web-20261113`; the QML files remain installed for
  manual fallback.

The reproducible unit and autostart files are in
[`deploy/`](deploy/). Their installed locations are:

```text
/etc/systemd/system/xytheta-hmi-web.service
/home/rpi/.config/systemd/user/xytheta-hmi-kiosk.service
/home/rpi/.config/labwc/autostart
```

Current-session verification included HTTP `200 OK`, a mapped Wayland
Chromium kiosk, one kiosk service, and the requested screens at 720×1280 with
no horizontal overflow or undersized visible buttons. A Chrome DevTools touch
test exercised Home → Tools → Optical registration, Run/Camera, Jog, Inspect →
Windows sync/Calibration profiles, explicit Back paths, and cancel/confirm
dialog dismissal. A cold reboot and physical finger contact were not performed
in this deployment session, so boot persistence and panel-level touch mapping
remain acceptance checks.

### Remote access

Tailscale is not currently installed or active on RPI4-HMI. If remote access is
added, keep the HMI server bound to loopback and proxy only its port through
Tailscale Serve rather than binding Python to `0.0.0.0`. The same browser UI can
then serve both the local touchscreen and an authenticated tailnet client
without exposing another controller or camera API.

The measured browser footprint while the UI-only deployment was active was
about **384 MiB proportional set size**, with **420 MiB** total system use and
about **1.4 GiB** available on the 2 GB Pi. Recheck this budget after adding
AprilTag processing, image storage, or a live-camera path. Do not run a second
full HMI locally merely to provide remote access.

## Navigation philosophy

**Android-style hierarchical navigation without Android's persistent navigation bar, a drawer, or bottom-tab menu.** A root **Home** dashboard gives four large touch tiles. Opening a tile moves into a functional screen. Each child screen has a top-left **Back** control, the browser/system Back key works, and desktop Escape/Backspace also navigates back (except when Backspace is editing a form field). The header and five-axis readout remain fixed; body content is independently scrollable when necessary, never covered by navigation chrome. During a simulated active run, contextual **Hold / Resume** and **Stop** are available in the top app bar, not hidden in a distant submenu.

Navigation hierarchy:

    Home
      ├─ Run
      │   ├─ Feed override
      │   └─ Camera (also under Tools)
      ├─ Jog (Pen XY / Camera ZB / Rotary A)
      ├─ Tools
      │   ├─ Optical registration
      │   ├─ Fiducial diagnostics
      │   ├─ Camera
      │   ├─ Pen tools / protected macros
      │   ├─ Coordinates / work zero
      │   └─ System status
      └─ Inspect
          ├─ Scan progress
          ├─ Windows sync & recovery
          ├─ Inspection results
          └─ Approved calibration profiles

Light high-contrast UI, solid high-visibility Run/Hold/Stop controls, ~55px minimum command button heights, readable disabled states, no misleading fake live feed, no pen-force DRO. Global compact DRO labels are **X/Y** (pen), **A** (rotary controller), **Z/B** (raw camera/CoreZB controller axes). In the current project, **A is motor-shaft degrees**, not an optically verified bed angle; do not silently relabel it as calibrated θ. The CoreZB mechanism must not be presented as Cartesian camera X/Y until the kinematics are actually commissioned. Actual feed reporting is distinct from commanded feed override.

## Workflow implemented as UI/demo states

1. **RUN:** start/resume, feed hold, confirmation-protected stop, commanded override 10–200% and reset to 100% (demo controls only).
2. **JOG:** select Pen XY / Camera ZB / Rotary A, step 0.1/1/10, directional pad, lockout unless known-safe Idle (demo only; actual soft limits and homing not commissioned).
3. **TOOLS → Optical registration:** center-first optical orbit fit → unique B00 east-side theta datum → outer-ring fiducials. Artwork remains taped to the bed; AprilTags must be visible. No Hall/center sensor is presumed on the camera gantry. The demo progresses through 5 steps.
4. **INSPECT:** after verified normal end and safe pen park, optical registration → artwork scan → queued still-image package → Windows analysis and validation → Pi commit or cancel/revert acknowledgment → gate release. In demo, System status offers a **Simulate verified job completion** test path, explicitly not an actual safety signal.
5. **SYNC:** Retry and confirmation-protected Cancel & Revert UI, pending-job lockout, and simulation of acknowledged resolution.
6. **PROFILES:** current and two prior approved generations. Candidate fitting and validation belong to Windows; Pi stores approved outcomes. Displayed demo profile IDs are illustrative, never actual profiles.

## Required production adapter (not implemented)

A **single authenticated Pi-local motion supervisor / sender** must own the RP23CNC connection, job lifecycle, CoreZB/Theta motion coordination, machine state and interlocks. The frontend must only call this supervisor; it must *not* create another independent grblHAL/ioSender connection. Before enabling any presently disabled action:

- Define a stable status/events API with freshness timestamps, controller state, pen-clear/full-retract and park acknowledgments, job hash, calibration/profile hash, camera CoreZB pose, encoder/step uncertainty, optical-registration confidence, queue checkpoint and Windows sync state.
- Define acknowledged commands, idempotency keys, rejection reasons and cancellation semantics for sender Run/Hold/Stop, protected P100/P116-style macros, jogs, camera capture, registration and synchronization. Distinguish sender stream completion from confirmed controller execution.
- Retain the existing **M2** program-end and toolhead retract/park handshake contract in docs/integration/INTERFACES.md. Completion requires normal full-program execution, sender drain, controller Idle, full pen clearance and machine-coordinate park; a textual M2 or 100%-streamed progress alone is insufficient. Physical E-stop remains independent.
- Reject jogs when machine is not safely Idle, and reject new G-code until the previous inspection outcome is committed or an explicit cancel/revert was acknowledged. No optimistic UI unlock.
- Calibrate camera intrinsics/extrinsics and CoreZB-to-machine mapping, confirm optical center/Theta zero against actual reference, protect against fiducial occlusion, and distinguish controller A coordinates from optical Theta angles.
- Store inspection metadata/images in bounded batches on Pi 4 (2GB); Windows owns full artwork-to-executed-G-code comparison and rolling candidate evaluation. The Pi handles lightweight AprilTag detection/orbit fitting and the image queue. Optional paper fiducials may help resolve paper slip but are not mandatory.
- Supply the camera preview/still/overlay endpoints without stretching imagery, plus scan and sync progress; the UI currently provides placeholders only.

**Do not activate motion buttons merely because a server responds.** Require an audited single-authority action contract, controller and toolhead safety testing, an explicit enablement mechanism, and on-device validation.

## Smoke tests

On a development machine with Node.js, run:

    node hmi/tests/smoke.cjs

The dependency-free smoke script checks offline lockouts, all 16 views, header
Hold/Resume, confirmation-gated simulated completion, registration, scanning,
sync, and direct-link Back fallback. It passed on Node.js 25.5.0 on the Windows
development host. Node.js is not installed on RPI4-HMI, and no package was
installed solely for this test. The deployed Chromium page was instead tested
through its loopback DevTools endpoint with coordinate-level touch input.

## Checks run on the first implementation

- JavaScript syntax compiled successfully.
- All 16 rendered views loaded through the navigation logic in a simulated DOM.
- Synthetic journey checked: Run → verified-completion confirmation → five registration steps → four scan increments → pending package → evaluation → submission gate unlocked.
- Contextual Hold action appeared on the header during a simulated active run.

**Not yet tested:** cold-boot persistence, physical finger/multitouch mapping,
focus trapping, touchscreen multi-hour stability, photo transfer performance,
Pi CPU/RAM during AprilTag detection, controller alarms, state staleness, any
real jog/macro/feed control, or calibration accuracy. Never confuse a tested
mock transition with a tested machine integration.

## Files

- [index.html](index.html) — accessible shell, app bar, five-axis DRO, content viewport.
- [styles.css](styles.css) — high-contrast portrait layout, nested menu cards, controls and confirmations.
- [app.js](app.js) — hierarchical router, Back support, view templates, explicit offline/demo safety behavior.
- [`deploy/`](deploy/) — installed systemd and labwc startup definitions.
- [Project HMI specification](../camera-inspection/touchscreen.md) — architecture, navigation and integration requirements.
