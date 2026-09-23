# Lab Note: 2026-09-23 - T-02 single-descend ten-cycle run

## Objective

Bench-validate the single-descend seek that replaced the two-touch sequence, and
measure its pulse count and held-force behaviour against the two-touch baseline.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A at 640 SPS, GP2 `LIFT_HOME` switch, installed pen over paper.
- Firmware: integrated `pro_micro_rp2350_toolhead` at commit `4312007`
  ("Replace the two-touch seek with a single descend").
- Interface: service UART1 GP20/GP21 at 115200 baud; one-shot `p` snapshots and
  default state events only.

## Procedure

Cold start at GP2, one `p` snapshot, then `e` for the first M3. Each further
cycle was one `l` and one `e`, with a `p` snapshot at `HOLD_FORCE` and another
once back in `LIFTED`.

## Results

Ten M3/M5 cycles completed with **no faults**: zero `FAULT_EVENT` lines.

| Cycle | Seek pulses | `HOLD_FORCE` entry | Snapshot force | Relief |
|---:|---:|---:|---:|---:|
| 1 (cold from GP2) | 56/100 | 177,861 | 170,669 | 0 / 0 ms |
| 2 | 24/100 | 226,059 | 172,855 | 1 / 20 ms |
| 3 | 26/100 | 219,855 | 181,290 | 4 / 80 ms |
| 4 | 26/100 | 217,596 | 176,653 | 16 / 331 ms |
| 5 | 23/100 | 220,959 | 163,892 | 17 / 351 ms |
| 6 | 26/100 | 219,180 | 161,982 | 18 / 369 ms |
| 7 | 22/100 | 162,289 | 154,147 | 18 / 369 ms |
| 8 | 24/100 | 210,533 | 154,347 | 19 / 390 ms |
| 9 | 26/100 | 226,026 | 161,663 | 23 / 477 ms |
| 10 | 24/100 | 222,016 | 167,765 | 27 / 556 ms |

The target is the absolute 176,357 raw (35 g), band 151,163-201,551 raw.

- Warm seek pulses: 22-26, essentially unchanged from the two-touch warm cycle
  count. The cold start dropped from 74 to 56.
- Held force: 154,147 to 181,290 raw, a 27,143 raw (about 5.4 g) spread, wider
  than the 13,738 raw (2.7 g) warm-cycle spread of the two-touch.
- M5 clear returned within 1,162 to 2,048 raw of the clear tare on every cycle.
- `cs1238_rejects` rose from 2 to 5 over the run with no fault.

## Difficulties and corrective actions

None required. No configuration or wiring change was made.

## Interpretation

The single descend works and is simpler, but it did not deliver the warm-cycle
latency improvement that motivated it. Warm M3 still needs 22-26 pulses because
most of them close the roughly 1.75 mm M5 clearance gap; removing the back-off
and retune removed only the tune portion of the old count.

The seek also overshoots its threshold. Most cycles entered `HOLD_FORCE` at
210,000-226,000 raw (42-45 g) against a 151,163 raw (30 g) threshold, because
one 5 ms fine pulse near contact can add more than ten grams. The hold loop and
the urgent relief then corrected the force down into the band, which is why
`urgent_relief_count` climbs over the run to 27 activations and 556 ms total.
The two-touch's tune phase had avoided that overshoot by landing at the band's
lower edge.

That overshoot-and-correct is the consistency cost: held force spread is about
5.4 g against 2.7 g before. For this non-precision machine it is tolerable, but
it is a real trade, not free.

## Decisions and next action

Keep the single descend; it is the right simplification and the cold start is
faster. The remaining latency is the clearance gap, which no seek change can
remove. The next step is T-01H clearance repeatability, followed by a
deterministic-clearance M3 that descends a known short distance in a few pulses.

If the overshoot bothers the result, a later refinement is a softer final
approach - shorter pulses or reduced PWM once the force is near the threshold -
rather than restoring the two-touch.

## References

- [T-02 in the test plan](../../testing/TEST_PLAN.md)
- [Replace the two-touch seek with a single descend](../../changes/rp23cnc-software/2026/2026-09-23-replace-two-touch-with-single-descend.md)
