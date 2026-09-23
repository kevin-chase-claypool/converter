# Lab Note: 2026-09-23 - T-02 ten-cycle run on the 300 ms + outlier-rejection build

## Objective

Confirm the 300 ms settle and the CS1238 outlier rejection across a longer M3/M5
cycle set, and verify that the false hard-force fault from a corrupt conversion
does not recur.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A at 640 SPS, GP2 `LIFT_HOME` switch, installed pen over paper.
- Firmware: integrated `pro_micro_rp2350_toolhead` at commit `3179f6b`
  ("Reject implausible CS1238 conversions"), which includes the 300 ms settle
  and the rejection logic.
- Interface: service UART1 GP20/GP21 at 115200 baud; one-shot `p` snapshots and
  default state events only.

## Procedure

Cold start at GP2, one `p` snapshot, then `e` for the first M3. Each further
cycle was one `l` and one `e`, with a `p` snapshot at `HOLD_FORCE` and another
once back in `LIFTED`.

## Results

Ten M3/M5 cycles completed with **no faults**: zero `FAULT_EVENT` lines.

| Cycle | `contact_ref_raw` | Target | `HOLD_FORCE` entry | Snapshot force | Tune pulses |
|---:|---:|---:|---:|---:|---:|
| 1 (cold from GP2) | 74,312 | 226,744 (clamped) | 204,199 | 202,495 | 59/100 |
| 2 | 80,032 | 226,744 (clamped) | 261,134 | 219,084 | 20/100 |
| 3 | 38,108 | 214,465 | 192,354 | 217,658 | 28/100 |
| 4 | 55,528 | 226,744 (clamped) | 209,842 | 231,396 | 24/100 |
| 5 | 69,242 | 226,744 (clamped) | 234,221 | 228,396 | 20/100 |
| 6 | 54,705 | 226,744 (clamped) | 236,082 | 223,062 | 20/100 |
| 7 | 60,813 | 226,744 (clamped) | 233,840 | 223,576 | 18/100 |
| 8 | 60,080 | 226,744 (clamped) | 234,717 | 228,159 | 22/100 |
| 9 | 58,946 | 226,744 (clamped) | 207,991 | 231,377 | 20/100 |
| 10 | 74,716 | 226,744 (clamped) | 230,491 | 230,518 | 15/100 |

Every cycle reported `ready=[contact:1 clear:0 gp27:0]` with `fault=none`.

- Held force, warm cycles only (2-10): 217,658 to 231,396 raw, a **13,738 raw
  (about 2.7 g)** spread. Including the cold start it is 202,495 to 231,396.
- First-touch reference: 38,108 to 80,032 raw, a 41,924 raw (about 8.3 g)
  spread. Eight of ten sit above the 50,387 raw clamp threshold, so the target
  is the same 226,744 raw for those cycles regardless of the reference.
- M5 clear returned within 1,163 to 2,870 raw of the clear tare on every cycle,
  inside the 3 g release band.

### Rejection activity

`cs1238_rejects` read 0 through cycle 8 and then 3 from cycle 9 onward. Three
implausible conversions were absorbed with no fault, which is exactly the
behaviour the rejection was added to provide. The previous run's false
hard-force trip did not recur.

The urgent relief engaged twice in cycle 2 only (`urgent_relief_count=2`,
`urgent_relief_ms=42`), and stayed flat for the remaining eight cycles.

## Difficulties and corrective actions

None required. No configuration or wiring change was made during the run.

## Interpretation

The 300 ms settle is acceptable for the seek. The metric that governs drawing
quality — held force — is as tight as or tighter than it was at 500 ms: warm
cycles span 2.7 g here against 3.4 g in the earlier nine-cycle 500 ms run.

The first-touch reference is looser and trends higher than at 500 ms, which is
the expected signature of under-reading during a shorter settle causing one
extra pulse. It does not propagate to the held force, because the target clamp
makes the target independent of any reference above 10 g, and the highest
reference (80,032 raw, 15.9 g) remains under the 20 g ceiling.

The cold-start cycle is still the outlier, as in every prior set: it took a
59-pulse tune and held low at 202,495 raw.

## Decisions and next action

Keep the 300 ms settle. The seek is now repeatable across 19 clean cycles on the
recent builds. The next gate is T-03 stationary force hold; the seek-side work
is done unless the cold-start overshoot warrants the two-settled-reading
tune-hand-off change.

## References

- [T-02 in the test plan](../../testing/TEST_PLAN.md)
- [Reduce the sensing settle to the measured 300 ms](../../changes/rp23cnc-software/2026/2026-09-23-reduce-settle-to-measured-300ms.md)
- [Reject implausible CS1238 conversions](../../changes/rp23cnc-software/2026/2026-09-23-reject-implausible-cs1238-samples.md)
