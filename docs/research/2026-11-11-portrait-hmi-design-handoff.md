# Portrait Plotter HMI — design handoff (2026-11-11)

**Status:** Design discussion and simulated UI prototypes only. No production HMI, converter, sender, or firmware changes implemented by this document.

## Purpose and physical platform

Preserve the decisions and unresolved implementation work from the 2026-11-11 ChatGPT HMI design thread for future implementation in this repository.

- Raspberry Pi 4 with official Raspberry Pi Touch Display 2, **720 × 1280 portrait**, intended as a thin-client touchscreen; Pi PoE+ HAT planned.
- rp23cnc / grblHAL motion controller accessed via Ethernet; ioSender is the current sender, possibly to be extended or coordinated with a supervisory host.
- ESP32-P4 Ethernet / MIPI-CSI camera device and Ryzen AI 9 365 laptop for image acquisition/processing. Live video pipeline and command routing **not yet validated**.
- Pen gantry: controller **X, Y**; rotating bed **A**; independent camera gantry intended to use controller **Z, B**. The camera's mechanical CoreXY arrangement must **not** be presented as Cartesian camera X/Y in the UI. The proposed five-axis mapping is **not the current commissioned configuration**: existing integration documentation says Z is unused; introducing Z/B requires a separately approved grblHAL build/configuration, wiring, and interface update.

## User-selected practical HMI

Three persistent navigation tabs: **Monitor / Analytics / Machine**. Inspection is a contextual subview, not a fourth primary tab. No scrolling at native 720×1280. Favor a high-contrast **light** UI: near-black/navy text on white/light-gray background, saturated blue navigation and macros, green Start/Resume, amber Pause, red Stop, visibly gray disabled controls. Solid buttons, high-contrast icons/text, strong outlines, and touch targets roughly 56–64 physical pixels where feasible. Avoid decorative card stacks, large wasted headings, and the dark telemetry panel.

Always-visible regions, from top to bottom:
1. Compact brand, connection/simulation and machine/job state.
2. Compact five-axis readout **X/Y/A (pen/bed)** and **Z/B (camera)** on *every* tab; do not duplicate an oversized dark DRO in Analytics.
3. One bounded content viewport, sized to fit without overlapping persistent controls.
4. Persistent high-visibility **Start/Resume, Pause, Stop** row with state-aware disabling; Stop requires confirmation.
5. Persistent Monitor / Analytics / Machine navigation row.

**Observed defect in prototype:** On an Android screenshot, Machine content overflowed into the bottom control dock: Reset Feed text clipped, protected macros covered, jog arrows too pale. Subsequent simulated redesign shortened feed override, used a compact jog pad and protected macros, and separated the bottom dock. **Actual 720×1280 pixel rendering, fonts, scaling, touch sizes and all-tab overflow still require on-device verification.** A ChatGPT interactive prototype is not production source code.

### Monitor
- Largest useful camera viewport, optional target/path overlay, in-process vision toggle, clear indication that demo camera content is simulated.
- Job progress and adaptive ETA, without competing with video.
- **Inspect Finished Plot** is disabled until *normal job completion* and controller idle, with verified pen clearance and bed registration. Manual user initiation only, followed by a confirmation with **Cancel — Do Nothing**. Do not auto-run a full-plot scan.
- Post-print scan view: coverage/progress, stop, results for missing strokes, extra marks, path deviation. Simulated example: 2 issues, max deviation 0.18 mm; **not a measured accuracy claim**.
- Demo-only **Simulate Plot Completion** control must not appear in production.

### Analytics
- No repeated large axis DRO and no dark telemetry box. Five-axis readout remains in persistent header.
- Time breakdown (drawing, rapid travel, pen cycles, **in-process** vision), ETA model/accuracy confidence and correction, remaining strokes, remaining path length, deviation/inspection metrics.
- Consider estimated-vs-actual completion trend if measured data becomes available.
- Keep post-print full-scan time separate from plotting ETA, since it is manual and optional.
- Simulated values shown in conversation are placeholders, not validated telemetry.

### Machine
- Feed override **10–200%**, clear percentage, compact slider and prominent reset-to-100 control.
- Jog selection **Pen XY / Camera ZB / Rotary A**; steps **0.1, 1, 10**; large directional controls. Z/B are raw controller axes, not camera Cartesian coordinates.
- Jog locked while running, inspecting, or otherwise not safely idle; show **JOG LOCKED — MACHINE NOT IDLE** or **INSPECTION ACTIVE**, rather than merely gray arrows.
- **Home & Register** and **Pen Lift & Park** protected macros, both confirmed with **Cancel — Do Nothing**. Production commands must follow existing P100/P116 and toolhead contracts; do not implement generic unsafe home/park.
- Connection health for rp23cnc, camera device, and host processing; clearly distinguish connectivity from controller state.
- WPos/MPos was only a cosmetic toggle in a prior prototype; implement real coordinate offsets or omit it.

## Completion detection and G-code contract — IMPORTANT CORRECTION

The conversation considered appending an explicit end marker and suggested **M30**. **That suggestion was not checked against this repository's established contract.** Current authoritative `docs/integration/INTERFACES.md` specifies **M2** as program end and a specific pre-end safety sequence: normal `M5` (PEN_CLEAR), required completion wait(s), full retract via `M65 P0` / `G65 P115 Q0` / `M64 P0`, then machine-coordinate `G53 G0 X Y` park, and **M2**. Do **not** replace this with a simplistic `M5; M30` footer or assume M5 alone means full retract. M3 means ENGAGE; M5 means PEN_CLEAR, not LIFT_HOME.

Proposed supervisory completion state machine:
1. Host/sender confirms **normal completion of the entire streamed job** (including existing M2 and all required completion/park blocks), not just a textual marker or 100% lines sent.
2. Controller reports actual **Idle** (not Hold, Alarm, Jog, Run, or disconnected); Idle alone is insufficient, because it can occur mid-job.
3. Verify required pen clearance/full retract and park completion from the existing toolhead handshake/status contract; do not infer physical clearance from M5 alone.
4. Validate required registration/homing and camera scan safety conditions.
5. Only then enable manual **Inspect Finished Plot**. User confirms; on cancel do nothing. Any abort, reset, sender error, alarm, disconnect, incomplete park or uncertain state invalidates completion.

**Implementation decision still open:** Determine how the selected ioSender version and grblHAL report program-end, stream drain, M2 execution, and toolhead/park completion; choose a reliable sender/supervisor event contract and test with normal end, early M2, feed hold, abort, alarm, reset, disconnect, and failed clearance. A G-code comment marker may help with diagnostics but cannot establish successful execution by itself. Preserve current M2 until evidence justifies an explicit coordinated change.

## Architecture and implementation work not yet done

- Determine who owns authoritative machine state, job lifecycle, and commands (ioSender vs supervisory laptop app vs Pi frontend); avoid simultaneous competing sender/controller connections.
- Implement robust sender→supervisor→Pi status and action APIs with acknowledged state transitions, stale-data/disconnect handling, and permission/confirmation rules.
- Build a production HMI at exact native portrait resolution with fixed vertical regions and per-tab fit testing; test in bright ambient light, including disabled-state legibility and gloved/finger touch.
- Integrate camera live stream, overlay alignment, in-process anomaly detection, and *separate* user-triggered finished-plot scan with safe motion orchestration.
- Commission proposed Z/B camera axis mapping and motion lockouts before enabling jog; ensure physical collision prevention, limits, and interlocks.
- Wire feed override to actual sender/controller semantics; validate MPos/WPos and axis units (A is **motor-shaft degrees** in current repository).
- Preserve current P100 homing/registration and P116 pen lift/park behavior. Do not assert unverified electrical connections, PoE power budget, camera autofocus compatibility, or realtime throughput.
- Add test cases for every tab and job state, modal cancellation, disabled buttons, completion/inspection gating, camera disconnect, and screen overflow.

## Handoff notes

The thread iterated through: light high-contrast theme → industrial/precision-console aesthetic → practical camera-first layout → high-visibility solid controls → removal of redundant dark Analytics DRO → Android screenshot showing overflow → compact fixed-dock Machine redesign → discussion of explicit end-of-job semantics. All prior UI previews were simulated ChatGPT interactive layouts; none are deployed to the Pi or committed as runnable UI source.

**Related authoritative files:** `docs/integration/INTERFACES.md`, `docs/START_HERE.md`, `software/README.md`, `firmware/README.md`, `docs/project/ROADMAP.md`. This note records a **future design** and must not be read as a change to those current contracts.
