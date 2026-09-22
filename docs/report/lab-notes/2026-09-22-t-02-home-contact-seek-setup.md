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

### First bounded seek result

After flashing the first home-origin candidate, the user issued `e`. It ended
safely at its 160-pulse budget rather than contacting paper:

```text
15:00:00.789 -> event=FAULT_EVENT pressure=FAULT cmd=M3 fault=M3 home contact seek pulse budget exhausted cs1238_raw=169277 cs1238_filtered=169004 cs1238_tare=249630 tare_valid=1 cs1238_delta=-80626 force_norm_raw=80626 hard_limit_raw=302326 lift_home=0 home_seek_pulses=160/160 mag=DISARMED mT=[0.136,0.146,0.146] delta=0.020 mag_samples=40465 status=0x00000473 ready=[contact:0 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
```

The pen was still physically about 4.5 mm above paper. The normalized force
was 80,626 raw, or approximately 16 g using the cap-free precision-weight
profile: below the 176,357 raw (35 g) contact threshold and far below the
302,326 raw (60 g) hard limit. This is a safe pulse-budget result, not a
contact-seek pass.

## Difficulties and corrective actions

The implementation assumed M3 would normally begin after M5 from a small
clearance gap, but the device currently starts at GP2 full retract. The first
5 ms / 250 ms candidate was also much too slow and short for the measured
distance: 800 ms total drive time covered only about 7.5 mm. Revise only the
home-seek pacing to 25 ms pulses and 50 ms sensing settles, with 80 pulses and
an 8-second ceiling. The CS1238 35 g target, 60 g hard limit, and post-contact
force-control cadence do not change.

## Interpretation

The reported position explains why a fixed 100 ms M3 move can fail to reach
paper from this state. The first pulse-budget fault gives a direct installed
mechanism result: approximately 7.5 mm per 800 ms of full-drive seek motion.
The revised 25 ms / 50 ms candidate should provide about 18.75 mm of bounded
travel in approximately six seconds at its 80-pulse ceiling. It still stops on
the calibrated contact threshold, a GP2-stuck guard, budget, timeout, sensor
loss, or hard-force limit. It must be checked on the real toolhead.

## Decisions and next action

Flash and supervise the updated integrated toolhead firmware. First verify a
one-shot `p` snapshot shows `pressure=LIFTED`, `lift_home=1`, a valid tare, and
no fault; then issue one `e` and observe the pulse count and state. Keep the
physical power cutoff reachable, and do not clear any fault until its cause
and pen position are checked. See T-02 and T-01J in
[`../../testing/TEST_PLAN.md`](../../testing/TEST_PLAN.md).
