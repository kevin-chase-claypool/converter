# Lab Note: 2026-09-23 - T-02 at 300 ms settle, and a CS1238 conversion glitch

## Objective

Exercise the 300 ms settle build through M3/M5 cycles, and record the fault
that ended the run.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A at 640 SPS, GP2 `LIFT_HOME` switch, installed pen over paper.
- Firmware: integrated `pro_micro_rp2350_toolhead` at commit `ce8dd6a`
  ("Reduce toolhead sensing settle to the measured 300 ms").
- Interface: service UART1 GP20/GP21 at 115200 baud; one-shot `p` snapshots and
  default state events only.

## Procedure

Cold start at GP2, one `p` snapshot, then `e` for the first M3. Each further
cycle was one `l` and one `e`, with a `p` snapshot at `HOLD_FORCE` and another
once back in `LIFTED`.

## Results

Two M3/M5 cycles completed before the run ended in a fault.

| Cycle | `contact_ref_raw` | Target | `HOLD_FORCE` entry | Snapshot force | Tune pulses | Relief |
|---|---:|---:|---:|---:|---:|---:|
| 1 (cold from GP2) | 24,236 | 200,593 | 194,229 | 190,646 | 74/100 | 0 / 0 ms |
| 2 | 48,557 | 224,914 | 218,558 | 205,871 | 21/100 | 0 / 0 ms |

Both cycles reported `ready=[contact:1 clear:0 gp27:0]` with `fault=none`, and
the urgent relief never engaged (`urgent_relief_count=0`). M5 completed cleanly
both times: `CLEARANCE_LIFT` to `CLEAR_TARE_SETTLING` to `LIFTED` with
`force_norm_raw` returning to 1,856 and 837 raw.

### The fault

While the toolhead sat idle in `LIFTED` after the second M5, the controller
faulted with no motor command outstanding:

```text
event=FAULT_EVENT pressure=FAULT cmd=M5 fault=hard force limit exceeded cs1238_raw=-6292478 cs1238_filtered=-107985 cs1238_tare=283471 tare_valid=1 cs1238_delta=-391456 force_norm_raw=391456 contact_ref_raw=48557 contact_ref_valid=1 hard_limit_raw=302326 lift_home=0 home_seek_pulses=26/100 home_tune_pulses=21/100 urgent_relief_count=0 urgent_relief_ms=0 mag=DISARMED mT=[0.126,0.117,0.170] delta=0.054 mag_samples=52246 status=0x00000473 ready=[contact:0 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
```

`cs1238_raw=-6292478` is not a force reading. The installed bridge spans roughly
-1.5e5 to +3.2e5 raw across its whole range, so this is a corrupt conversion.
One such sample inside the 16-sample average is enough: fifteen samples near
+277,000 and one at -6,292,478 average to about -133,000, which matches the
reported `cs1238_filtered=-107985` and the resulting `force_norm_raw=391456`
that exceeded the 302,326 raw hard limit.

This is a different failure from the two earlier hard-force trips, where
`cs1238_raw` and `cs1238_filtered` agreed with each other and the force rise was
real. Here the raw is six million counts away from the filtered value.

## Difficulties and corrective actions

The run was cut short by a false hard-force fault caused by a single corrupt
ADC conversion. No configuration or wiring change was made; the fault is in the
acquisition path's tolerance of outliers.

Corrective action: reject implausible conversions before they enter the moving
average, and fault only if they persist. See
[`reject-implausible-cs1238-samples`](../../changes/rp23cnc-software/2026/2026-09-23-reject-implausible-cs1238-samples.md).

## Interpretation

The 300 ms settle produced no fault of its own across the two completed cycles.
Both reached `HOLD_FORCE` in band with no relief activity, and both M5 clears
returned to within about 2,000 raw of the clear tare.

Two cycles are not enough to judge the settle change. The reference spread here
is 24,321 raw (24,236 to 48,557), slightly wider than the 21,403 raw spread of
the nine-cycle 500 ms run, but cycle 1 of every cold-start set has been the
outlier, and cycle 1 here reached only 24,236 raw after a 74-pulse tune. A
comparison needs the same cold-start-plus-warm structure in both sets.

The glitch is worth noting beyond this run: it also explains the isolated
-353,842 raw sample seen in the E-09E kitchen-scale trace. Corrupt conversions
are a recurring property of this acquisition path, not a one-off.

## Decisions and next action

Reflash with the outlier rejection and repeat the cycle set. Watch
`cs1238_rejects` in the `p` snapshots: a small, slowly growing count is expected
and harmless, while a fast-growing count or a
`CS1238 reading implausible` fault indicates the CS1238 interface itself needs
attention — supply decoupling, clock/trace integrity, or a longer conversion
settle in the driver.

## References

- [T-02 in the test plan](../../testing/TEST_PLAN.md)
- [E-09E post-pulse settle trace](2026-09-23-e09e-post-pulse-settle-trace.md)
- [T-02 hysteresis-relief nine-cycle run](2026-09-23-t-02-hysteresis-relief-nine-cycle-run.md)
