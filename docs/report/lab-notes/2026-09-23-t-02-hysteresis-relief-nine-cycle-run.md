# Lab Note: 2026-09-23 - T-02 hysteresis relief nine-cycle run

## Objective

Verify the hysteresis-corrected over-force relief across repeated M3/M5 cycles,
and record whether the relief engages and settles.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A at 640 SPS, GP2 `LIFT_HOME` switch, installed pen over paper.
- Firmware: integrated `pro_micro_rp2350_toolhead` at commit `dec3e5d`
  ("Add hysteresis to the urgent over-force relief"), which includes the 500 ms
  settled seek, the band-headroom clamp, the urgent relief, its activation
  counters, and the corrected trigger and stop points.
- Interface: service UART1 GP20/GP21 at 115200 baud, one-shot `p` snapshots and
  default state events only; the `v` stream was off.
- Gates: `commission=[dir:1 pressure:1 lift:0 mag:0]` throughout.

## Procedure

Cold start at GP2, one `p` snapshot, then `e` for the first M3. Each further
cycle was one `l` and one `e`, with a `p` snapshot once the cycle reached
`HOLD_FORCE`.

## Results

Nine M3/M5 cycles completed with **no faults**: zero `FAULT_EVENT` lines.

| Cycle | `contact_ref_raw` | Target (clamped) | Relief trigger | `HOLD_FORCE` entry | Snapshot force | Tune pulses |
|---|---:|---:|---:|---:|---:|---:|
| 1 (cold from GP2) | 38,620 | 214,977 | 265,365 | 282,165 | 199,658 | 23/100 |
| 2 | 56,790 | 226,744 (clamped) | 277,132 | 227,441 | 221,620 | 16/100 |
| 3 | 56,803 | 226,744 (clamped) | 277,132 | 212,165 | 207,410 | 9/100 |
| 4 | 43,928 | 220,285 | 270,673 | 210,415 | 209,868 | 17/100 |
| 5 | 55,257 | 226,744 (clamped) | 277,132 | 208,540 | 214,773 | 16/100 |
| 6 | 52,801 | 226,744 (clamped) | 277,132 | 208,468 | 217,021 | 5/100 |
| 7 | 48,806 | 225,163 | 276,163 | 209,949 | 204,385 | 19/100 |
| 8 | 60,023 | 226,744 (clamped) | 277,132 | 212,666 | 209,657 | 16/100 |
| 9 | 50,543 | 226,744 (clamped) | 277,132 | 213,817 | 213,760 | 17/100 |

Every cycle reported `ready=[contact:1 clear:0 gp27:0]` with `fault=none`.

- First-touch reference spread: 38,620 to 60,023 raw, **21,403 raw (about
  4.2 g)**.
- Held force spread at snapshot: 199,658 to 221,620 raw, **21,962 raw (about
  4.4 g)**.
- Smallest margin to the 60 g hard limit: 80,706 raw (about 16 g).
- The target clamp engaged on six of the nine cycles; references above the
  50,387 raw (10 g) clamp threshold are now the common case rather than the
  exception, and every clamped cycle still held inside its band.

### Relief engagement

The new counters show the relief engaging exactly once in this run, entirely
inside cycle 1, and then never again across the remaining eight cycles:

```text
urgent_relief_count=0 urgent_relief_ms=0     (pre-run snapshot)
urgent_relief_count=9 urgent_relief_ms=199   (every snapshot from cycle 1 on)
```

Cycle 1 entered `HOLD_FORCE` at 282,165 raw, which is 67,188 raw (13.3 g) above
its 214,977 raw target and above its 265,365 raw relief trigger, so the relief
engaged immediately on entering hold. It took nine bounded activations totalling
199 ms of driving to bring the force back inside the band; the snapshot then
read 199,658 raw, comfortably in band. Cycles 2 through 9 did not trigger the
relief at all.

```text
STATE_EVENT pressure=HOME_TUNE_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=38645
STATE_EVENT pressure=HOLD_FORCE cmd=M3 lift_home=0 tare_valid=1 force_norm_raw=282165
event=SNAPSHOT pressure=HOLD_FORCE cmd=M3 fault=none cs1238_raw=32046 cs1238_filtered=31317 cs1238_tare=230975 tare_valid=1 cs1238_delta=-199658 force_norm_raw=199658 contact_ref_raw=38620 contact_ref_valid=1 hard_limit_raw=302326 lift_home=0 home_seek_pulses=43/100 home_tune_pulses=23/100 urgent_relief_count=9 urgent_relief_ms=199 mag=DISARMED mT=[0.102,0.185,0.112] delta=0.077 mag_samples=33215 status=0x00000c63 ready=[contact:1 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
```

## Difficulties and corrective actions

None in this run. Two points are worth recording without over-reading them:

- Cycle 1 is again the cold-start cycle and again the variable one. Its tune
  threshold was 189,783 raw, yet it entered `HOLD_FORCE` at 282,165 raw, so the
  force rose about 92,000 raw past the threshold before the hold state was
  entered. The relief absorbed that, but the overshoot itself is unaddressed.
- Every one of the eight warm cycles entered `HOLD_FORCE` between 208,468 and
  227,441 raw, close to or below its target, with no relief activity. The
  overshoot is confined to the cold start.
- Nine relief activations averaging about 22 ms each means the relief stopped
  and restarted repeatedly rather than retracting once. It converged and the
  counters then stayed flat, so the hysteresis correction is working, but the
  stop-at-band-edge condition lets a still-rising mechanism re-trigger.

## Interpretation

This is the first run in which the relief demonstrably engaged on hardware, and
the sequence still completed with no faults. The cycle that had previously
faulted twice on the hard limit - a cold-start cycle entering hold well above
target - was instead recovered by the relief and settled in band.

Nine consecutive cycles completed without a fault, which is the longest clean
sequence recorded on this toolhead. The counters also confirm the earlier
hunting report was not relief activity: cycles 2 through 9 show
`urgent_relief_count` unchanged at 9 and 199 ms, so the relief never fired
during them.

## Decisions and next action

Continue building repeat evidence toward the T-01H 30-cycle count; nine cycles
are recorded here. Watch
`urgent_relief_count` between snapshots: a flat count means a cycle needed no
relief, and a growing count means the mechanism again entered hold above target.

If cycle 1 keeps overshooting into hold, the next change is at the tune
hand-off - requiring the settled value to remain inside the target band across
two consecutive settled readings before declaring contact - rather than any
further change to the relief.

## References

- [T-02 in the test plan](../../testing/TEST_PLAN.md)
- [T-02 five-cycle clean pass](2026-09-23-t-02-five-cycle-clean-pass.md)
- [Add hysteresis to the urgent over-force relief](../../changes/rp23cnc-software/2026/2026-09-23-add-hysteresis-to-urgent-relief.md)
