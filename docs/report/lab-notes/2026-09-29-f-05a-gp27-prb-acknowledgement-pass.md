# Lab Note: 2026-09-29 - F-05A GP27/PRB pen-transition acknowledgement

## Objective

Validate the commissioned GP27/`PRB` pen-transition acknowledgement on the
installed hardware: that `P115 Q0` accepts a verified initial clear, that
`P115 Q1` observes a fresh inactive-then-active edge after each `M3` and `M5`,
that a held-high or never-asserting level raises `error[39]`, and that the
published level stays steady through `HOLD_FORCE`. Home the pre-check that
found the contact-ready level toggling (see
[`2026-09-29-f-05a-gp27-contact-state-flap.md`](2026-09-29-f-05a-gp27-contact-state-flap.md)).

## Configuration

- Hardware revisions: RP23CNC / `RP23U5XBB` V1.01; SparkFun Pro Micro RP2350
  toolhead with the PC817C three-channel interface board (`U3` = GP27 return).
- Wiring/pin map: GP27 -> module `J2.6` -> `U3` -> module `J1.6` `PROBE SIG` ->
  RP23CNC `PROBE SIG`/`PRB`. See `WIRING_TABLE.md` rows `TH-001A-RT`,
  `TH-003D`, and `PROBE_MICRO_JST_HARNESS.md` (`J-PC817`).
- Firmware commit/build: toolhead
  `firmware/pen_pressure/pro_micro_rp2350_toolhead` at commit `1affc99`
  (`CONTACT_READY_LOST_MS` hysteresis, `RPSW-20260929-001`); controller
  grblHAL `1.1f.20260908` homing candidate.
- grblHAL settings: `$6=1` (invert probe), `$16=1` (invert spindle enable).
- Converter settings/sample: none; commands came from the ioSender console and
  the two helper programs listed below.
- Instruments: none. Evidence is the controller status stream, the toolhead
  service console, and the controller's probe input indicator.

## Code, commands, and configuration used

```text
Controller build identity, ioSender:
  $I
    [VER:1.1f.20260908:]
    [OPT:VNMHSL,100,1024,4,0]
    [AXS:4:XYZA]
    [NEWOPT:ENUMS,RT+,HOME,ES,REBOOT,EXPR,TC,SED,ETH,FTP,YM,SD]
    [SIGNALS:HSEP]
    [BOARD:RP23U5XBB]
    [DRIVER:RP2350@150MHz]
    [PLUGIN:FS stream v1.15]
    [PLUGIN:FS macro plugin v0.24]
    [PLUGIN:SDCARD v1.28]

Toolhead service console (Arduino IDE, COM8 at 115200):
  p     one status snapshot

Transition-edge probe, streamed as a program
(samples/gcode/f05a-q7-edge-check.gcode):
  G21 G90
  M64 P0
  M5
  G4 P3.0
  M3
  G65 P115 Q7 B12
  M5
  G4 P2.0
  M64 P0

Strict acceptance pass, streamed as a program
(samples/gcode/f05a-p115-strict-pass.gcode):
  G21 G90
  M64 P0
  M5
  G4 P3.0
  G65 P115 Q0
  M3
  G65 P115 Q1 B12
  M5
  G65 P115 Q1
  M64 P0

Failure paths, single console lines:
  G65 P115 Q1        (stale-high and never-asserts cases)

Independent input proof:
  dry contact between PROBE SIG and PROBE GND
```

## Procedure

1. Parked the pen at GP2 with `M64 P0`, `M5`, `M65 P0`, `G4 P3.0`, `M64 P0`,
   `M5` and confirmed the toolhead was in a publishing state with `p`.
2. Confirmed the controller status showed `Pn:ZAP` at that moment.
3. Ran `G65 P115 Q7` from the parked clear state.
4. Streamed `samples/gcode/f05a-q7-edge-check.gcode` so the macro was already
   polling while the toolhead physically moved.
5. Streamed `samples/gcode/f05a-p115-strict-pass.gcode` and read the console.
6. Ran the stale-high failure path from a held `M3`.
7. Disconnected the `PROBE SIG` conductor and confirmed the probe read
   unasserted, then ran the never-asserts failure path.
8. Proved the controller input independently by dry-contacting `PROBE SIG` to
   `PROBE GND`.

## Results

Parked clear-ready, toolhead:

```text
event=SNAPSHOT t_ms=670694 pressure=LIFTED cmd=M5 fault=none
cs1238_raw=249836 cs1238_filtered=250450 cs1238_tare=0 tare_valid=0
cs1238_delta=250450 force_norm_raw=-250450 hard_limit_raw=377908
lift_home=1 home_seek_pulses=0/100 warm_ema=0 urgent_relief_count=0
urgent_relief_ms=0 recoveries=0 cs1238_rejects=0 cs1238_last_reject=0
mag=DISARMED mT=[0.146,0.380,0.327] delta=0.085 mag_samples=335121
status=0x0000146f ready=[contact:0 clear:1 det:0]
commission=[dir:1 pressure:1 lift:0 mag:1]
```

`status=0x0000146f` has `CLEAR_READY` set with both cores ready, the tool
lifted, safe-for-homing, TMAG online and baselined, and CS1238 online. The
controller status line read `Pn:ZAP`.

Held contact state, 10 s after `M3`:

```text
event=SNAPSHOT t_ms=549151 pressure=HOLD_FORCE cmd=M3 fault=none
cs1238_raw=46219 cs1238_filtered=49505 cs1238_tare=243036 tare_valid=1
cs1238_delta=-193531 force_norm_raw=193531 hard_limit_raw=377908
lift_home=0 home_seek_pulses=41/100 warm_ema=0 urgent_relief_count=0
urgent_relief_ms=0 recoveries=0 cs1238_rejects=591
cs1238_last_reject=-8265780 mag=DISARMED status=0x00000c63
ready=[contact:1 clear:0 det:0] commission=[dir:1 pressure:1 lift:0 mag:1]
```

`force_norm_raw=193531` is inside the 30-60 g ready band around the 226745
target, so `contact:1` is a legitimate reading rather than hysteresis masking a
lost hold. The pre-fix toggling did not recur after the `1affc99` build.

`Q7` from the parked clear state:

```text
[MSG:P115 Q7 release missing: GP27 stayed asserted through the release bound]
[MSG:P115 Q7 completion observed]
```

`Q7` across the streamed `M3` transition:

```text
[MSG:P115 Q7 release observed]
[MSG:P115 Q7 completion observed]
```

The status stream showed `Pn:ZAP` -> `Pn:ZA` -> `Pn:ZAP` across that run.

Strict pass, three acknowledgements and no error:

```text
[MSG:P115 toolhead completion acknowledged]
[MSG:P115 toolhead completion acknowledged]
[MSG:P115 toolhead completion acknowledged]
```

That is `Q0` on the verified initial clear, `Q1` after `M3`, and `Q1` after
`M5`. Both transitions showed `Pn:ZA` between `ZAP` readings.

Failure path, stale high (`Pn:ZAP`, pen held in `M3`):

```text
[MSG:P115 command completion did not clear its prior ready state]
[MSG:Warning: error 39 in macro P115.macro]
error:39 - Value out of range.
```

Failure path, never asserts (`PROBE SIG` conductor disconnected, `Pn:ZA`, and
`Q7` reporting release observed with completion missing):

```text
[MSG:P115 toolhead ready acknowledgement timed out]
[MSG:Warning: error 39 in macro P115.macro]
error:39 - Value out of range.
```

Independent input proof: dry-contacting `PROBE SIG` to `PROBE GND` flipped the
controller from `Pn:ZA` to `Pn:ZAP`. The toolhead's `U3` output measured
0.147 V and 0.172 V from `PROBE SIG` to `CTRL_GND` while the controller's probe
input indicator was lit; the recorded `U3` bench figure for an asserted output
is about 0.2 V.

## Difficulties and corrective actions

- An early DMM reading of "0 V" from `PROBE SIG` to `CTRL_GND` was a
  misreading of the meter. It briefly misdirected the session toward a wiring
  fault; the corrected 0.147 V and 0.172 V readings are normal `U3` saturation
  voltages and the input was never at fault.
- Single-line MDI sends cannot exercise a transition edge: the toolhead's seek
  finishes before the operator can send the next line, so the macro only ever
  sees the settled state. Both helper programs above are streamed so the macro
  is already polling while the pen moves. This is a procedure requirement, not
  a defect.
- A stale `M3` left asserted after a full retract made the toolhead re-engage
  the moment it reached GP2. That is the documented `LIFTED` behaviour while
  GP29 still commands engage, corrected by releasing the command (`M5`) before
  the retract.
- Repeated status lines that showed no `P` bit were sampled during seeks or
  other non-ready states, not during a fault. Confirming the toolhead's own
  `ready=[...]` field at the same moment is what distinguishes the two.

## Interpretation

F-05A is satisfied on the installed hardware. The controller reads GP27 through
`U3` correctly, `Q0` accepts a verified initial clear, `Q1` observes a genuine
fresh inactive-to-active edge on both transitions, and both failure modes raise
`error[39]` rather than allowing the program to run on. The toolhead's own
ready flags agree with the controller-visible level in both stable states.

Two items remain open and are not covered by this pass:

1. The intermittent `error[39]` seen during real printing, approximately once
   per hour, was not reproduced. The operator reports the probe input indicator
   normally tracking toolhead activity, so the failure is a rare lost or late
   level rather than a broken path. The contact-ready release hysteresis in
   `RPSW-20260929-001` is the targeted mitigation and still needs a real print
   run to prove.
2. The controller's settings have drifted from the documented snapshot:
   `$21=1` (documented `0`), `$24=1000.0` and `$25=4000.0` (documented `50`
   and `500`), `$110=10000.000` and `$111=10000.000` (documented `1500`), and
   `$131=451.000` (documented `446.000`). These are not part of F-05A and are
   recorded as an open discrepancy against
   `firmware/grblhal/config/machine-settings.md` and
   `firmware/grblhal/config/build-record.md`.

## Decisions and next action

- F-05A is recorded as passed in `docs/testing/TEST_PLAN.md`; see change note
  `RPSW-20260929-002`.
- The converter's **Wait for GP27 toolhead ready** option is now unblocked but
  deliberately unchanged: it stays off by default until the project owner
  decides, since the hourly miss above is unresolved.
- Next: run a real print with the handshake enabled and the recover option on,
  capturing the toolhead live stream and the controller console, and record
  what the toolhead is doing at the moment an `error[39]` occurs.
