# Lab Note: 2026-09-23 - T-02 five-cycle clean pass

## Objective

Re-run the T-02 contact seek across repeated M3/M5 cycles on the build with the
band-headroom clamp and the urgent over-force relief, and record the result.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A at 640 SPS, GP2 `LIFT_HOME` switch, installed pen over paper.
- Firmware: integrated `pro_micro_rp2350_toolhead` at commit `f6ec62c`
  ("Add bounded urgent over-force relief to the hold loop"), which includes the
  500 ms settled seek, the band-headroom clamp, and the urgent relief.
- Interface: service UART1 GP20/GP21 at 115200 baud, one-shot `p` snapshots and
  default state events only; the `v` stream was off.
- Gates: `commission=[dir:1 pressure:1 lift:0 mag:0]` throughout.

## Procedure

Cold start at GP2, one `p` snapshot, then `e` for the first M3. Each further
cycle was one `l` and one `e`, with a `p` snapshot after the cycle reached
`HOLD_FORCE` and another once back in `LIFTED`.

## Results

Five M3/M5 cycles completed with **no faults**: zero `FAULT_EVENT` lines and
zero `pressure=FAULT` states across the whole capture.

| Cycle | `contact_ref_raw` | Target (clamped) | Band top | `HOLD_FORCE` entry | Snapshot force | Seek pulses | Tune pulses |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 (cold from GP2) | 41,246 | 217,603 | 242,797 | 199,154 | 195,203 | 82/100 | 75/100 |
| 2 | 42,915 | 219,272 | 244,466 | 207,574 | 205,030 | 9/100 | 5/100 |
| 3 | 52,012 | 226,744 (clamped) | 251,938 | 212,448 | 208,146 | 26/100 | 11/100 |
| 4 | 43,359 | 219,716 | 244,910 | 206,367 | 202,217 | 25/100 | 20/100 |
| 5 | 39,722 | 216,079 | 241,273 | 194,192 | 202,757 | 26/100 | 8/100 |

Every cycle reported `ready=[contact:1 clear:0 gp27:0]` with `fault=none`.

- First-touch reference spread: 39,722 to 52,012 raw, **12,290 raw (about
  2.4 g)**.
- Held force spread at snapshot: 195,203 to 208,146 raw, **12,943 raw (about
  2.6 g)**.
- Smallest margin to the 60 g hard limit: 94,180 raw (about 18.7 g).

Cycle 1 complete trace:

```text
event=SNAPSHOT pressure=LIFTED cmd=M5 fault=none cs1238_raw=292057 cs1238_filtered=290587 cs1238_tare=0 tare_valid=0 cs1238_delta=290587 force_norm_raw=-290587 contact_ref_raw=0 contact_ref_valid=0 hard_limit_raw=302326 lift_home=1 home_seek_pulses=0/100 home_tune_pulses=0/100 mag=DISARMED mT=[0.097,0.161,0.126] delta=0.062 mag_samples=5363 status=0x0000046f ready=[contact:0 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
STATE_EVENT pressure=HOME_SEEK_CONTACT cmd=M3 lift_home=1 tare_valid=0 force_norm_raw=-288687
STATE_EVENT pressure=HOME_RELEASE_TARE_SETTLING cmd=M3 lift_home=0 tare_valid=0 force_norm_raw=-221032
STATE_EVENT pressure=HOME_SEEK_CONTACT cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=-14
STATE_EVENT pressure=HOME_RETRACT_AFTER_TOUCH cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=41246
STATE_EVENT pressure=HOME_TUNE_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=41292
STATE_EVENT pressure=HOLD_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=199154
event=SNAPSHOT pressure=HOLD_FORCE cmd=M3 fault=none cs1238_raw=45619 cs1238_filtered=45326 cs1238_tare=240529 tare_valid=1 cs1238_delta=-195203 force_norm_raw=195203 contact_ref_raw=41246 contact_ref_valid=1 hard_limit_raw=302326 lift_home=0 home_seek_pulses=82/100 home_tune_pulses=75/100 mag=DISARMED mT=[0.170,0.180,0.136] delta=0.061 mag_samples=40680 status=0x00000c63 ready=[contact:1 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
```

Cycle 3, where the target clamp engaged:

```text
STATE_EVENT pressure=HOME_RETRACT_AFTER_TOUCH cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=52012
STATE_EVENT pressure=HOME_TUNE_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=52095
STATE_EVENT pressure=HOLD_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=212448
event=SNAPSHOT pressure=HOLD_FORCE cmd=M3 fault=none cs1238_raw=67812 cs1238_filtered=67530 cs1238_tare=275676 tare_valid=1 cs1238_delta=-208146 force_norm_raw=208146 contact_ref_raw=52012 contact_ref_valid=1 hard_limit_raw=302326 lift_home=0 home_seek_pulses=26/100 home_tune_pulses=11/100 mag=DISARMED mT=[0.209,0.166,0.141] delta=0.076 mag_samples=75357 status=0x00000c63 ready=[contact:1 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
```

## Difficulties and corrective actions

None in this run. Note what it does and does not exercise:

- The band-headroom clamp engaged on cycle 3. That reference (52,012 raw)
  exceeds the 50,387 raw clamp threshold, so the target was capped at
  226,744 raw and the cycle still held inside the clamped band.
- The urgent over-force relief produces no state event and does not change the
  pressure state, so whether it engaged during these cycles cannot be
  confirmed from this log. All five snapshots sat below their targets, so the
  hold loop was not in an over-force condition when the snapshots were taken.

## Interpretation

This is the first clean multi-cycle T-02 result: five consecutive M3/M5 cycles
reached `HOLD_FORCE` in band with no hard-force trip or any other fault.

Both scatter metrics that motivated the earlier work are now small. The
first-touch reference spread is 12,290 raw, against 45,706-195,497 raw before
the 500 ms settle. The held force spread is 12,943 raw, against the
250,000-300,000 raw excursions that were faulting.

The run does not prove the intermittent hard-force fault is gone. The previous
cycle set passed three of four and faulted on the fourth, and the failing
cycle's discriminating characteristic was an anomalous `HOLD_FORCE` entry
value (275,752 raw) far above its own snapshot (203,297 raw). No such spike
appeared here.

## Decisions and next action

T-02's seek is now repeatable across a supervised cycle set. Continue with
additional cycles toward the T-01H 30-cycle target and, when the paper drag is
acceptable, move to the T-03 stationary hold before attempting translation or
rotation.

Because the relief is invisible in telemetry, add an activation counter to the
`p` snapshot before the next long batch, so a re-run can show whether relief is
doing work or whether the mechanism has simply stopped running away.

## References

- [T-02 in the test plan](../../testing/TEST_PLAN.md)
- [T-02 settled-seek four-cycle run](2026-09-23-t-02-settled-seek-four-cycle-run.md)
- [Add bounded urgent over-force relief](../../changes/rp23cnc-software/2026/2026-09-23-add-urgent-over-force-relief.md)
