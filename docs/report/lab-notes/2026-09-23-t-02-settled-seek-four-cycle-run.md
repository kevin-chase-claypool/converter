# Lab Note: 2026-09-23 - T-02 settled-seek four-cycle run

## Objective

Verify the 500 ms settled-force contact seek on the installed toolhead across
repeated M3/M5 cycles, and record the remaining failure mode.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A at 640 SPS, GP2 `LIFT_HOME` switch, installed pen over paper.
- Firmware: integrated `pro_micro_rp2350_toolhead` with commit `a3900b5`
  ("Settle toolhead contact seek on settled force") flashed.
- Interface: service UART1 GP20/GP21 at 115200 baud, one-shot `p` snapshots
  and default state events only; the `v` stream was left off.
- Gates: `commission=[dir:1 pressure:1 lift:0 mag:0]` throughout.

## Procedure

Cold-started at GP2, confirmed one `p` snapshot, then issued `e` for the first
M3. Each subsequent cycle was one `l` followed by one `e`, with a `p` snapshot
after the cycle reached `HOLD_FORCE`.

## Results

| Cycle | `contact_ref_raw` | Entered `HOLD_FORCE` at | Snapshot force | Seek pulses | Tune pulses | Band top |
|---|---:|---:|---:|---:|---:|---:|
| 1 (cold from GP2) | 38,886 | 261,273 | 228,772 | 86/100 | 78/100 | 240,437 |
| 2 | 46,551 | 199,644 | 223,750 | 22/100 | 9/100 | 248,102 |
| 3 | 42,697 | 213,280 | 206,046 | 26/100 | 19/100 | 244,248 |
| 4 | 78,727 | 238,853 | 240,184 | 29/100 | 4/100 | 280,278 |

`home_seek_pulses` counts seek and tune pulses together, so cycle 1's seek
travel was 8 pulses and the remainder were fine-tune steps.

Cycle 1 complete trace:

```text
STATE_EVENT pressure=LIFTED cmd=M5 lift_home=1 tare_valid=0 force_norm_raw=0
STATE_EVENT pressure=HOME_SEEK_CONTACT cmd=M3 lift_home=1 tare_valid=0 force_norm_raw=-259848
STATE_EVENT pressure=HOME_RELEASE_TARE_SETTLING cmd=M3 lift_home=0 tare_valid=0 force_norm_raw=-192641
STATE_EVENT pressure=HOME_SEEK_CONTACT cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=-172
STATE_EVENT pressure=HOME_RETRACT_AFTER_TOUCH cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=38886
STATE_EVENT pressure=HOME_TUNE_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=38986
STATE_EVENT pressure=HOLD_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=261273
```

Cycle 4 and its fault:

```text
STATE_EVENT pressure=HOME_RETRACT_AFTER_TOUCH cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=78727
STATE_EVENT pressure=HOME_TUNE_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=78732
STATE_EVENT pressure=HOLD_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=238853
event=SNAPSHOT pressure=HOLD_FORCE cmd=M3 fault=none cs1238_raw=24913 cs1238_filtered=24874 cs1238_tare=265058 tare_valid=1 cs1238_delta=-240184 force_norm_raw=240184 contact_ref_raw=78727 contact_ref_valid=1 hard_limit_raw=302326 lift_home=0 home_seek_pulses=29/100 home_tune_pulses=4/100 mag=DISARMED mT=[0.180,0.146,0.102] delta=0.039 mag_samples=239324 status=0x00000c63 ready=[contact:1 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
event=FAULT_EVENT pressure=FAULT cmd=M3 fault=hard force limit exceeded cs1238_raw=-47105 cs1238_filtered=-38343 cs1238_tare=265058 tare_valid=1 cs1238_delta=-303401 force_norm_raw=303401 contact_ref_raw=78727 contact_ref_valid=1 hard_limit_raw=302326 lift_home=0 home_seek_pulses=29/100 home_tune_pulses=4/100 mag=DISARMED mT=[0.219,0.156,0.097] delta=0.077 mag_samples=239536 status=0x00000473 ready=[contact:0 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
```

## Difficulties and corrective actions

Cycle 4 accepted a 78,727 raw first touch, roughly double the other three. That
put its acceptance band top at 280,278 raw, only 22,048 raw below the 302,326
raw hard limit. The force then rose from the 240,184 raw snapshot to 303,401
raw with the motor asleep and entered `FAULT`.

The tune pulse counts also varied by more than an order of magnitude across
cycles (78, 9, 19, 4), which is direct evidence that the force change per 5 ms
pulse is not stable on this mechanism.

Corrective action: clamp the relative target so the top of the acceptance band
always keeps 10 g below the hard limit. See
[`clamp-hold-band-below-hard-limit`](../../changes/rp23cnc-software/2026/2026-09-23-clamp-hold-band-below-hard-limit.md).

## Interpretation

The 500 ms settle fixed the measurement problem it was aimed at. The first
three cycles accepted a first touch between 38,886 and 46,551 raw, a 7,665 raw
(about 1.5 g) spread. Before that change the same figure ranged from 45,706 to
195,497 raw across cycles.

The remaining fault is not a measurement error. It is a margin problem: the
relative target moved the whole acceptance band upward with the touch
reference, and at a 15.6 g reference only 4.4 g of headroom remained, which
the post-hold creep consumed. Three of four cycles completed M3 to `HOLD_FORCE`
with `ready=[contact:1 clear:0 gp27:0]` and no fault.

M5 clear also repeated cleanly on all three completed cycles: `CLEARANCE_LIFT`
to `CLEAR_TARE_SETTLING` to `LIFTED` with `force_norm_raw` returning to within
about 300 raw of zero.

## Decisions and next action

Reflash the integrated toolhead with the clamped-target build and repeat the
M3/M5 cycle set. The pass criterion is unchanged: `HOLD_FORCE` with
`fault=none` and `ready=[contact:1 ...]`, but the band top must now stay at or
below 251,938 raw regardless of the accepted reference. If a cycle still runs
away after the clamp, the hold loop's relief rate is the next target rather
than the reference cap.

## References

- [T-02 in the test plan](../../testing/TEST_PLAN.md)
- [Settle the home contact seek on settled force](../../changes/rp23cnc-software/2026/2026-09-22-settle-contact-seek-on-settled-force.md)
- [Clamp the hold band below the hard-force limit](../../changes/rp23cnc-software/2026/2026-09-23-clamp-hold-band-below-hard-limit.md)
