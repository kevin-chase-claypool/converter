# Lab Note: 2026-09-22 - E-09E installed-pen kitchen-scale direction check

## Objective

Confirm the sign of the CS1238 response under the actual upward pen-tip reaction before assigning any production force-control direction or threshold. This is the first data point in the installed-pen force-path check, not a new transfer calibration.

## Configuration and procedure

- Test: E-09E installed-pen kitchen-scale pulse check, with the installed 300 g load cell, CS1238 channel A/gain 128/640 SPS, and kitchen scale under the installed pen.
- Controller: SparkFun Pro Micro RP2350 running `e09e_cs1238_pen_scale_pulse.ino` through GP20/GP21 3.3 V service UART, using Arduino IDE Serial Monitor at 115200 baud.
- Calibration relationship: accepted E-09C applies downward mass to the motor mount; this test measures the opposite, upward pen-tip reaction.
- The operator manually issued bounded single N20 pulses and allowed the scale to settle before reading CS1238. Exact pulse count and selected duration were not recorded in this first observation.

## Measurement

```text
PULSE_READING,time_us=145916961,raw=-59087,tare_delta=-312723,tare_valid=1
kitchen_scale_g=40.7

PULSE_READING,time_us=409351417,raw=5999,tare_delta=-247637,tare_valid=1
kitchen_scale_g=62.5

PULSE_DONE,direction=UP,ms=10,fault_during_drive=0,down_pulses_remaining=24
kitchen_scale_g_before_up_pulse=35.5

PULSE_READING,time_us=438954829,raw=187766,tare_delta=-65870,tare_valid=1
kitchen_scale_g_after_up_pulse=2.2
```

The implied clear-state tare is `253,636 raw` (`-59,087 - -312,723`).

## Outcome

The raw response is negative relative to tare while the scale measures a positive upward pen reaction. This confirms the **opposite** force direction selected for the E-09C downward-mass projection. One installed-pen point cannot establish linearity, hysteresis, repeatability, or the safe pulse/control envelope, so it does not replace the accepted known-mass slope or alter the production profile.

The observed magnitudes are not monotonic enough to construct an installed-pen transfer fit: the 40.7 g datum has a `-312,723 raw` delta while the later 62.5 g datum has a smaller `-247,637 raw` delta. This is evidence of a changing mechanism/settling state, not a valid linear calibration. The 10 ms up pulse then reduced the displayed scale reading from 35.5 g to 2.2 g without a fault, showing that 10 ms is too coarse near the 40–60 g target. E-09E therefore changes to 5–100 ms pulses in 5 ms steps. The original 40.7 g magnitude (`312,723 raw / 40.7 g = 7,684 raw/g`) remains materially different from the downward motor-mount calibration's `5,038.77 raw/g`.

### 5 ms loading trace

After the 5 ms E-09E update, the operator reported the following settled
loading observations. All records share the same reported tare validity; raw
delta is the recorded `tare_delta`, not a reconstructed value.

| Time | Scale g | Raw | Tare delta raw | Assessment |
|---|---:|---:|---:|---|
| 10:28:07 | 0.4 | 236,844 | -14,854 | low-force baseline region |
| 10:28:38 | 0.8 | 230,985 | -20,713 | low-force baseline region |
| 10:28:57 | 10.7 | 225,501 | -26,197 | low-force point; does not follow later slope |
| 10:29:15 | 35.8 | 120,294 | -131,404 | transitional point |
| 10:29:48 | 41.3 | -20,366 | -272,064 | target-region point |
| 10:30:08 | 41.5 | -4,371 | -256,069 | target-region point |
| 10:30:33 | 59.2 | -32,792 | -284,490 | target-region point |
| 10:30:58 | 64.1 | -76,157 | -327,855 | high-force trace |
| 10:31:20 | 64.9 | -84,198 | -335,896 | high-force trace |
| 10:31:41 | 66.3 | -88,560 | -340,258 | high-force trace |
| 10:32:17 | 67.3 | -353,842 | -605,540 | exclude: isolated raw outlier |
| 10:32:45 | 68.1 | -97,324 | -349,022 | high-force trace; returns to trend |
| 10:33:06 | 68.5 | -100,542 | -352,240 | high-force trace |
| 10:33:32 | 70.0 | -103,990 | -355,688 | high-force trace |

The 64.1–70.0 g non-outlier end of the trace is locally consistent: the raw
delta changes from `-327,855` to `-355,688` across 5.9 g, or approximately
`4,717 raw/g`. That is close to the cap-free downward-mass result of
`5,038.77 raw/g`. The precision-weight E-09C fit remains the sole raw-to-force
calibration authority. This kitchen-scale trace is deliberately not fitted or
used to replace its slope: the kitchen scale and compliant installed pen path
are only a coarse installed-direction/range check.

### 5 ms unloading trace

The operator then used 5 ms UP pulses and recorded the following unloading
path. Clear-state readings returned to within `+11,146` to `+13,006 raw` of
the original tare, which is inside the staged 3 g (`15,116 raw`) release band.

| Time | Scale g | Raw | Tare delta raw |
|---|---:|---:|---:|
| 10:37:25 | 69.5 | -105,591 | -357,289 |
| 10:37:41 | 68.8 | -100,667 | -352,365 |
| 10:37:55 | 68.0 | -96,288 | -347,986 |
| 10:38:09 | 67.4 | -92,251 | -343,949 |
| 10:38:27 | 66.6 | -84,996 | -336,694 |
| 10:38:41 | 65.9 | -82,983 | -334,681 |
| 10:38:57 | 65.0 | -78,205 | -329,903 |
| 10:39:13 | 63.6 | -70,944 | -322,642 |
| 10:39:26 | 52.5 | -62,118 | -313,816 |
| 10:39:43 | 40.4 | 80,943 | -170,755 |
| 10:39:58 | 41.0 | 88,681 | -163,017 |
| 10:40:37 | 20.0 | 112,318 | -139,380 |
| 10:41:05 | 0.4 | 232,764 | -18,934 |
| 10:41:20 | 0.0 | 264,704 | +13,006 |
| 10:41:38 | 0.0 | 262,844 | +11,146 |

The 69.5–63.6 g segment is again locally consistent and overlaps the loading
trace. The trace also exposes material mechanical hysteresis below about 60 g:
the same approximate 40–50 g scale region spans `-170,755` through `-313,816`
raw delta depending on approach history. That affects later controller tuning,
but does not invalidate the precision-weight calibration. The 50 g target
candidate (`-251,938 raw`) remains the selected center from that authoritative
fit; the kitchen-scale trace verifies it is in the practical working region.

## Difficulties and next action

The optional Windows application did not complete its adapter-COM connection, so Arduino IDE Serial Monitor provided explicit one-pulse commands and readable raw results. The first 5 ms load/unload cycle now reaches a stable clear return. No further kitchen-scale curve fitting is required: the next measurement work is controller dynamics, using the existing precision-weight raw profile and checking that the installed pen remains approximately in the requested 40–60 g range. Do not enable `PRESSURE_CALIBRATION_VALID`, actuator control, M3/M5 force control, or GP27 normal status from this observation alone.

## References

- [E-09C test plan](../../testing/TEST_PLAN.md)
- [E-09C cap-free known-mass result](2026-09-22-e-09c-cap-free-repeat.md)
- [E-09E serial monitor change](../../changes/rp23cnc-software/2026/2026-09-22-add-e09e-serial-monitor-shortcuts.md)
