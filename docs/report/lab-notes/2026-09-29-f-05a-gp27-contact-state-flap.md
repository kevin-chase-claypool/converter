# Lab Note: 2026-09-29 - F-05A dry-contact check: GP27/PRB toggles in the contact state

## Objective

Characterize the controller-visible GP27/`PRB` pen-transition level in each
toolhead pen state before running the strict `P115 Q0`/`Q1` F-05A pass, and
determine whether the level is steady enough for the macro's release-then-
completion edge check.

## Configuration

- Hardware revisions: RP23CNC / `RP23U5XBB` V1.01; SparkFun Pro Micro RP2350
  toolhead with the PC817C interface board (U3 = GP27 return channel).
- Wiring/pin map: GP27 -> PC817C U3 -> RP23CNC `PRB`. See `WIRING_TABLE.md`
  row `TH-001A-RT`. Controller `$6=1` for the normally-open PRB sink.
- Firmware commit/build: toolhead
  `firmware/pen_pressure/pro_micro_rp2350_toolhead` at commit `0236470`
  (`GP27_NORMAL_STATUS_ENABLED = true`, `GP27_TRANSITION_LOW_MS = 50`).
  `P115.macro` not yet installed; this step only watches the level.
- grblHAL settings: `$16=1` (invert spindle enable), `$6=1` (invert probe).
- Converter settings/sample: none; the two pen commands were sent from the
  ioSender console.
- Instruments: none. Evidence is the controller status stream plus the
  toolhead service console.

## Code, commands, and configuration used

```text
ioSender console, in order:
  m5
  m3

Observed status field: Pn:  (P = probe input, PRB / GP27 through U3)
```

## Procedure

1. Toolhead powered and fault-free; pen installed and clear of the paper.
2. Sent `m5` and watched the controller status stream until the level settled.
3. Sent `m3` and watched the status stream through the seek and hold.

## Results

After `m5`, `Pn:P` settled asserted and stayed there:

```text
<Idle|MPos:0.000,0.000,0.000,0.000|Bf:100,1023|FS:0,0|Pn:ZA>
<Idle|MPos:0.000,0.000,0.000,0.000|Bf:100,1023|FS:0,0|Pn:ZA>
<Idle|MPos:0.000,0.000,0.000,0.000|Bf:100,1023|FS:0,0|Pn:ZAP>
<Idle|MPos:0.000,0.000,0.000,0.000|Bf:100,1023|FS:0,0|Pn:ZAP|Ov:100,100,100>
```

After `m3`, the probe bit asserted during the seek and then **toggled**
between asserted and released while the pen sat in contact hold:

```text
<Idle|...|Pn:ZA>          (seek)
<Idle|...|Pn:ZA>
<Idle|...|Pn:ZA>
<Idle|...|Pn:ZA|WCO:...>
<Idle|...|Pn:ZAP>         (contact)
<Idle|...|Pn:ZAP>
<Idle|...|Pn:ZAP|WCO:...>
<Idle|...|Pn:ZA>          (released)
<Idle|...|Pn:ZA>
<Idle|...|Pn:ZAP>
<Idle|...|Pn:ZAP>
<Idle|...|Pn:ZA>
<Idle|...|Pn:ZAP>         (alternating to the end of the capture)
<Idle|...|Pn:ZA>
<Idle|...|Pn:ZAP>
...
```

All reports showed `Idle` and `MPos:0.000,0.000,0.000,0.000`; no motion was
commanded, and no fault was reported. The `Z` and `A` bits are the unwired Z
and A inputs and are unrelated.

## Difficulties and corrective actions

- What was observed: the GP27/`PRB` level is steady in the clear state but
  chatters in the contact state. This fails the interface contract that the
  only LOW is the seek/lift transition, and it makes `P115 Q1` capable of a
  false acknowledgement or an unlucky completion timeout.
- How it was diagnosed: reading `publishNormalPrintStatus()` against
  `updateReadyState()`. The ready flag asserted after three filtered
  conversions (about 4.7 ms) and reset on any single conversion outside the
  ±15 g band, while the hold loop that corrects an excursion operates on a
  250 ms cadence. The release path was therefore roughly 50x faster than the
  recovery it was meant to tolerate.
- What changed: release hysteresis, committed as `RPSW-20260929-001`. The
  level is now held through any excursion inside the 20 g urgent-relief bound
  and released only after 500 ms beyond it.
- Repeat result: not yet available. This note records the pre-fix observation;
  the post-fix re-check is the next action and F-05A stays open.

## Interpretation

The flapping is a firmware-side contract violation, not a bench mistake, and
it is a plausible contributor to the intermittent handshake failures seen
since the handshake default was tried. It is not on its own a complete
explanation of the `plane.gcode` completion timeout, which needs the level to
stay low for the whole bound rather than to toggle.

## Decisions and next action

- Fix recorded as `RPSW-20260929-001`; `P115.macro` still must not be enabled
  in the converter until F-05A passes.
- Next: flash the hysteretic build, repeat the `M3` + `Pn:` observation, and
  confirm `Pn:P` and the toolhead's `ready=[contact:1 ...]` both stay steady
  through `HOLD_FORCE`. Run the toolhead `v` live stream at the same time so a
  steady `ready` with a toggling `Pn` would isolate the remaining fault to the
  GP27/U3/`PRB` path.
