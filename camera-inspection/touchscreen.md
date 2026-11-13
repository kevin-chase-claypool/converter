# Raspberry Pi Touch Display 2 — HMI specification (November 2026)

**Implementation status:** The standalone, runnable frontend now lives in [../hmi/](../hmi/README.md). It has navigation, responsive layout and an explicitly marked interactive simulation. **Not deployed to the Pi; not attached to a live sender, motor controller, camera or calibration service.** Hardware actions remain disabled outside mock mode.

## Device and design system

- Official Touch Display 2 connected directly to Raspberry Pi 4 (2 GB); target **720×1280 portrait**. Orientation, touch mapping, kiosk startup and exact physical fit must be validated on-device.
- Material/Android-inspired **hierarchical screens**, **not** Android's bottom navigation/menu drawer and **not** four persistent tabs. Large **Home** buttons lead to Run, Jog, Tools and Inspect. Nested features have an explicit Back button; browser/system Back and Escape also work.
- Light high-contrast interface, readable typography, strong disabled states, large touch targets; fixed compact app bar and five-axis readout. The content area can scroll when necessary, but bottom navigation never overlays it.
- Contextual Hold/Resume and Stop buttons remain available in the top app bar during active plotting (once real control is integrated). Physical E-stop remains independent.

## Navigation tree

    Home
      Run
        Feed override
        Camera view
      Jog
        Pen XY / Camera ZB / Rotary A (mode selector inside Jog)
      Tools
        Optical registration
        Fiducial diagnostics
        Camera
        Pen tools and protected macros
        Coordinate references and work zero
        System status
      Inspect
        Scan progress
        Windows synchronization / recovery
        Stroke comparison results
        Calibration profile history

These are feature screens, not permanent nav tabs. Back returns to the prior page; a deep-linked screen falls back to its parent.

## Persistent information

- Header: current screen name, Back if nested, and **real/simulation/offline** connection indicator.
- Compact raw-controller DRO: **X/Y pen axes**, **A rotary controller axis**, **Z/B CoreZB raw axes**; no invented pen force reading. In the existing repository A uses **motor-shaft degrees**; it is not the same thing as optically verified bed θ. Final controller-to-bed conversion must be explicit.
- Status/footer: connection certainty, next-G-code submission gate; never infer permission from incomplete status.
- No unverified WPos/MPos toggle. Do not present user-selectable camera Cartesian X/Y until the mechanical CoreZB kinematic transform has been implemented and checked.

## Functional screens

### Run
- File, progress, ETA when credible, camera preview/still thumbnail, Start/Resume/Hold/Stop.
- Stop confirmation with **Cancel — Do Nothing**; state-aware enablement.
- Feed override 10–200%, ±10%, 100% reset; distinguish commanded override from actual reported feed.
- New job remains locked until previous post-print calibration/synchronization transaction is resolved and Pi acknowledged.

### Jog
- Pen XY, camera raw ZB, or rotary A selection; increments 0.1/1/10, direction arrows.
- Lockouts for Run, Hold, inspection, errors, controller uncertainty, disconnected state and uncommissioned Z/B soft limits. The frontend demo changes displayed numbers only.
- No direct browser-to-controller stream; only one sender/motion authority.

### Tools
- Optical registration with steps: (1) home CoreZB and establish calibrated pose; (2) estimate **physical bed center first** from multi-angle ring observations; (3) align uniquely coded B00 to the east station for optical θ=0°; (4) inspect ring; (5) save confidence/measurements. **Drawing/paper remains taped down**. All 20 peripheral tags must be unobstructed as needed.
- Fiducial diagnostics: 20 distinct B00–B19 identities, visibility/quality/position and capture errors.
- Camera: selectable preview, still and overlay views, no stretched image, clearly separated fake/real imagery.
- Protected controller macros: existing P100/P116 registration and pen park flows where still applicable, with safety confirmations. Preserve physical retract/park semantics; M5 alone does not prove full retract.
- Coordinate frames and diagnostics: X/Y/A/Z/B, optical center and zero, calibration uncertainty and camera-to-machine mapping.

### Inspect
- After normal program end **M2**, sender-drained completion, controller Idle, confirmed full pen clearance/park, automatically run optical registration, ring check and post-print artwork capture. The HMI reflects a state machine: drawing, registering, scanning, waiting for Windows, evaluating, committed/ready, failure/recovery. Never automatically start after an abort or mere "100% streamed" indication.
- Scanning progresses through bounded still-image captures; images and machine poses are queued persistently on the Pi until resolved. Registration does not require removing the completed drawing. Dedicated paper fiducials are **optional**; ambiguous paper slip must be reported rather than aligned away.
- Windows receives queued captures and the executed-stroke manifest, compares expected G-code to observed ink and evaluates calibration candidates. **Windows**, not the Pi, is the authoritative full-artwork analysis and model-fitting host.
- Sync view shows pending transaction, connectivity and progress. **Retry Sync** and confirmation-protected **Cancel Sync & Revert**, with acknowledgment and rollback to last approved profile. New-job gate releases only after committed/acknowledged resolution.
- Profiles show N current, N−1 and N−2 approved generations; automatically prune older unreferenced generations. No unverified metrics or fake approvals.

## Integration and safety boundaries

- The UI is presently **front-end only**. All hardware actions are offline-disabled; optional demo mode performs no network or hardware calls.
- A Pi-hosted **single sender/motion supervisor** must provide trustworthy status, event timestamps, image endpoints, fault codes, commands, acknowledgments and explicit job lock state. The browser, ESP32-P4 and Windows must not independently own motion.
- Existing program end uses **M2**, not generic M30. Honor machine-coordinate park and toolhead handshake from [../docs/integration/INTERFACES.md](../docs/integration/INTERFACES.md). Physical E-stop is separate.
- Pi 4 handles lightweight AprilTag detection, rotary orbit fitting, capture coordination and sync queue; heavy observed-vs-expected matching and rolling profile evaluation run on Windows.
- No real motion actions enabled until their actual controller semantics, limits and physical interlocks have been validated and the backend adapter implemented.

## Acceptance and testing

- Navigable Home/Run/Jog/Tools/Inspect and nested paths; explicit Back and OS/keyboard Back support; no bottom nav or drawer.
- Readable 720×1280 layout across all screens; check overflow, touch sizes, dialogs and active Hold/Stop on the actual Pi.
- Verify simulations never send commands and cannot be confused with real hardware telemetry.
- Test normal M2 completion, early M2, hold, abort, alarm, reset, disconnect, failed pen park and uncertain camera/controller status; reject unsafe inspection starts.
- Test registration failure on occluded/missing B00/tags and CoreZB not homed; verify optically determined center then zero and correct controller coordinates.
- Test queuing across disconnections, restart persistence, retry, cancel/revert, profile mismatch and no premature next-job unlock.
- Test image acquisition/AprilTag CPU and RAM on the **2 GB Pi 4**, bounded image memory and UI responsiveness.

See [../hmi/README.md](../hmi/README.md) for local launch and demo instructions.
