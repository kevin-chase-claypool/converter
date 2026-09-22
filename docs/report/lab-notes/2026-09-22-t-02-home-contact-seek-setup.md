# Lab Note: 2026-09-22 - T-02 home-origin seek setup

## Objective

Record the initial full-retract-to-paper condition that exposed why the
integrated M3 short move was insufficient, and capture the user-observed
starting state before running the new supervised seek.

## Configuration

- Hardware revisions: SparkFun Pro Micro RP2350 toolhead; installed N20/DRV8833,
  CS1238 load cell, GP2 lift-home switch, installed pen.
- Wiring/pin map: integrated toolhead harness; GP2 is active-low at the switch.
- Firmware commit/build: prior checked-in `pro_micro_rp2350_toolhead` build;
  the new home-origin seek source had not been flashed at the time of the
  observation.
- grblHAL settings: not involved; service UART used.
- Converter settings/sample: not involved.
- Instruments: one-shot serial status snapshot; physical gap estimated by user.

## Code, commands, and configuration used

No motor command was issued in this setup observation. The user supplied the
following serial snapshot and estimated the tip-to-paper separation at about
12 mm:

```text
14:22:35.275 -> event=SNAPSHOT pressure=LIFTED cmd=M5 fault=none cs1238_raw=254197 cs1238_filtered=254761 cs1238_tare=279348 tare_valid=1 cs1238_delta=-24587 force_norm_raw=24587 hard_limit_raw=302326 lift_home=1 mag=DISARMED mT=[0.156,0.166,0.136] delta=0.036 mag_samples=109947 status=0x0000046f ready=[contact:0 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
```

## Procedure

1. Read the current device snapshot over the Pro Micro service UART.
2. Report the approximate tip-to-paper gap at the full retract position.
3. Do not issue M3/e while determining whether the currently flashed firmware
   has enough travel to reach the paper.

## Results

- Snapshot reports `pressure=LIFTED`, `cmd=M5`, `fault=none`,
  `tare_valid=1`, and `lift_home=1`.
- The user estimates the pen is about 12 mm from paper while at GP2 full retract.
- No motor movement or contact attempt was reported in this observation.
- This is far beyond the previously staged 100 ms M3 move, which was based on
  the roughly 1.75 mm ordinary M5 clearance gap, not the cold-start distance.

## Difficulties and corrective actions

The implementation assumed M3 would normally begin after M5 from a small
clearance gap, but the device currently starts at GP2 full retract. Add a
separate bounded, sensor-checked home-origin seek rather than extending the
100 ms move into a blind drive. The new source has not yet been flashed or
tested on hardware.

## Interpretation

The reported position explains why a fixed 100 ms M3 move can fail to reach
paper from this state. The current implementation adds an isolated home-seek
path that stops on the calibrated contact threshold, a GP2-stuck guard, pulse
budget, timeout, sensor loss, or hard-force limit. The pulse-to-distance
estimate is provisional; it must be checked on the real toolhead.

## Decisions and next action

Flash and supervise the updated integrated toolhead firmware. First verify a
one-shot `p` snapshot shows `pressure=LIFTED`, `lift_home=1`, a valid tare, and
no fault; then issue one `e` and observe the pulse count and state. Keep the
physical power cutoff reachable, and do not clear any fault until its cause
and pen position are checked. See T-02 and T-01J in
[`../../testing/TEST_PLAN.md`](../../testing/TEST_PLAN.md).
