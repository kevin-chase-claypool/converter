# XY-Theta Touch Display 2 HMI — navigable frontend

**Status: committed, runnable browser UI only.** There is **no live sender, motion supervisor, ESP32-P4 image service, calibration store, or Windows synchronization API** connected to these screens yet. The frontend deliberately never sends motor commands, G-code, machine macros, or synthetic calibration approvals.

## Launch on the Pi (or a desktop for review)

Run from the repository root:

    cd hmi
    python3 -m http.server 8080 --bind 127.0.0.1

Open **http://127.0.0.1:8080/** in Chromium. For a dedicated Pi kiosk, open the URL with Chromium's --kiosk flag once screen orientation, touch mapping, startup, screen blanking, and display scaling have been verified. The interface targets the official **720×1280 portrait Touch Display 2**, is responsive to smaller browser windows, and uses no external JavaScript/CSS libraries.

**Interactive demo:** open **http://127.0.0.1:8080/?demo=1** or use **Home → System status → Try interactive demo**. Every screen is marked **SIMULATION** and every motion-related interaction changes *only* local mock state. Demo exists to exercise navigation, confirmation dialogs, lockouts and scan/sync progress before backend integration. No demo state is a measurement, captured image or successful hardware command. Without demo mode, the screen says **OFFLINE** and all hardware actions are unavailable.

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

The dependency-free smoke script checks offline lockouts, all 16 views, header Hold/Resume, confirmation-gated simulated completion, registration, scanning, sync, and direct-link Back fallback. The same test logic was exercised in a sandboxed JavaScript harness during authoring; on-device browser and physical hardware tests are still outstanding.

## Checks run on the first implementation

- JavaScript syntax compiled successfully.
- All 16 rendered views loaded through the navigation logic in a simulated DOM.
- Synthetic journey checked: Run → verified-completion confirmation → five registration steps → four scan increments → pending package → evaluation → submission gate unlocked.
- Contextual Hold action appeared on the header during a simulated active run.

**Not yet tested:** actual Touch Display 2 720×1280 rendering/touch, Chromium kiosk lifecycle, focus trapping, touchscreen multi-hour stability, photo transfer performance, Pi CPU/RAM during AprilTag detection, controller alarms, state staleness, any real jog/macro/feed control, or calibration accuracy. Never confuse a tested mock transition with a tested machine integration.

## Files

- [index.html](index.html) — accessible shell, app bar, five-axis DRO, content viewport.
- [styles.css](styles.css) — high-contrast portrait layout, nested menu cards, controls and confirmations.
- [app.js](app.js) — hierarchical router, Back support, view templates, explicit offline/demo safety behavior.
- [Project HMI specification](../camera-inspection/touchscreen.md) — architecture, navigation and integration requirements.
