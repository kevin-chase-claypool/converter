# ioSender-to-Converter Compatibility Review

**Review date:** 2026-09-05
**Scope:** SVG converter output, ioSender 2.0.47 streaming, installed RP23CNC
grblHAL baseline, and the intended `G65 P100 Q0` startup path.

## Result

The intended workflow is compatible in principle, but it is **not ready for
unconditional “convert, run P100, then print” operation**. ioSender is an
appropriate sender for grblHAL and does not need a translation layer; the
remaining discrepancies are in the converter defaults, program modal-state
header, uncommissioned P100 prerequisites, and unverified machine/toolhead
behavior.

## Confirmed compatible subset

The converter's intended non-Z output uses `G21`, `G90`, `G0`/`G1` with `X`,
`Y`, `A`, and `F`, `M3`, `M5`, `G4 P<seconds>`, and `M2`. This is within the
grblHAL G-code subset recorded in the repository's F-02 parser dry run. The
official [ioSender repository](https://github.com/terjeio/ioSender) describes
ioSender as a G-code sender for grblHAL/Grbl with program-running, settings,
and macro support. grblHAL declares `G94` as the default units-per-minute feed
mode and supports `G21`, `G90`, `G54`, `M3`/`M5`, and `M2` in its official
[G-code definitions](https://github.com/grblHAL/core/blob/master/gcode.h).

## Discrepancies and blockers

| Priority | Finding | Evidence | Required resolution |
|---|---|---|---|
| Stop | **The converter defaults to Z mode.** A default conversion emits `G0 Z5` and `G1 Z0`, not the required `M5`/`M3` pen contract. This machine has no wired Z motor. | `Settings.include_z = True`; a default generated program contains Z commands. The software documentation instead instructs the operator to uncheck Use Z axis. | Change the default to non-Z M3/M5 mode and add a regression test. Until then, the operator must manually clear **Use Z axis** before every conversion. |
| Stop | **The generated header omits `G94` and `G54`.** P100 currently sets both, but a drawing program should establish its own feed and work-coordinate modes. | The generated header is `G21`, `G90`, then `G0 F...`; the macro contains `G21 G90 G94 G17 G54`. A prior Y test produced error 22 until `G94` was explicitly sent. | Emit at least `G21`, `G90`, `G94`, and `G54` before any motion. Retain `G17` if the converter assumes that plane. |
| Stop | **P100 Q0 cannot currently be the automatic startup step.** | `P100.macro` sets `#<commissioned> = 0` and aborts Q0. The installed baseline build configuration has `PROBE_ENABLE=0`, while the macro requires probe input, NGC expressions, filesystem macros, Aux0, and PRB. | Build/install the stated candidate features, commission constants and sensor-to-pen offset, then pass F-08, E-18, M-08, M-09, and M-10 before enabling Q0. |
| Stop | **M3/M5 pen behavior is not yet authorized for production strokes.** | Firmware documentation leaves F-05/E-18 mapping and normal M5 clearance validation open; T-01H/T-01J remain required. | Verify actual spindle-enable polarity, M3 contact, M5 clearance, dwell values, and repeated no-drag cycles. |
| Hold | **Radius-aware combined X/Y/A timing remains a host-side estimate.** | The converter computes a coordinated feed from mixed X/Y/A motion. The repository keeps M-06 open. grblHAL's official changelog records a rotary-feed-rate fix, but the installed build record does not state whether its relevant option is enabled. | Run M-06 after X rate and M-03 calibration. Compare commanded blocks, actual elapsed time, and position repeatability at inner/mid/outer radii. Do not rely on preview runtime for production scheduling before this pass. |
| Hold | **X-axis limits, scaling, homing, and complete plot envelope are unfinished.** | X rate and X M-03 dimensional calibration are open; homing/limits and coordinated motion remain open in the roadmap. | Finish X M-02/M-03 and homing/limit validation before allowing an unattended file run. |

## Required self-contained program contract

After the converter-default and header fixes above, every saved drawing file
should begin with a self-contained modal/safety preamble equivalent to:

```gcode
G21
G90
G94
G17
G54
M5
G4 P<configured pen-up dwell in seconds>
```

It should then use only `G0/G1 X/Y/A F`, `M3`, `M5`, `G4 P...`, and final `M2`.
`A` remains motor-shaft degrees. The file must not contain Z words for the
force-controlled configuration.

## Safe operator sequence after all gates pass

1. Connect ioSender to the confirmed RP23CNC grblHAL build and verify `Idle`.
2. Run `G65 P100 Q0`; require its explicit successful completion message and
   `G54 X0 Y0 A0` ready state. Do not stream a drawing after an abort.
3. Load the converted file, inspect the first lines for the self-contained
   preamble and absence of Z words, then use ioSender's preview/3D view as a
   path sanity check.
4. Stream the program with the pen in its tested profile. `M3` engages contact;
   `M5` confirms clear before travel.

## External-source note

ioSender does not compensate for missing program modes or disabled controller
features; it streams the program to grblHAL. The official grblHAL source marks
`G94` as the default feed mode, while its
[changelog](https://github.com/grblHAL/core/blob/master/changelog.md) records
rotary-feed handling as a build/configuration concern. Therefore the generated
file must explicitly establish its modes, and M-06 remains the authoritative
machine-side verification for this mixed linear/rotary plotter.
