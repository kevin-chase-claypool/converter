# Lab Note: 2026-10-01 - lowering the A-axis rate limit to what the bed can hold

## Objective

Stop asking the 12:1 bed for angular rates it cannot follow. The converter used
to assume the controller's configured `$113` (80000 motor deg/min = 1333 motor
deg/s = 110.8 bed deg/s, about 21 m/min of pen surface speed at the 185 mm rim)
and emitted drawing moves that hit that cap, including 561 motor deg (46.6 bed
deg) inside a single move at radii of 0.35-9.1 mm. The bed lags, the stroke
being drawn bends, and every contour after it is rotated by the lost angle -
which is the fan of rows around the bed centre in the 2026-10-01 print and the
"waveforms drifting into adjacent waveforms" reported before it.

This note records the settings before the change, the change itself, and the
acceptance test. It is the machine-side half of `WSW-20261001-010`.

## Configuration

- Hardware revisions: RP23CNC / `RP23U5XBB` V1.01; X/Y 20T GT2 at 16x
  microstepping, A 8x; bed ratio 12.03324 motor deg per bed deg
  (4331.9664 motor deg per revolution).
- Wiring/pin map: unchanged by this test.
- Firmware commit/build: the grblHAL build reporting `$300=grblHAL` as dumped
  below.
- grblHAL settings: full dump below (before).
- Converter settings/sample: converter at `9be772a`
  (`WSW-20261001-010`), which caps its own A requests at 20000 motor deg/min.
- Instruments: ioSender console and DRO; visual alignment of two pen marks.

## Code, commands, and configuration used

`$$` dump before the change (2026-10-01, ioSender):

```text
$0=5.0      $1=25       $2=0        $3=0        $4=15       $5=0
$6=1        $9=1        $10=511     $11=0.010   $12=0.002   $13=0
$14=6       $15=0       $16=1       $17=0       $18=0       $19=0
$20=1       $21=1       $22=3       $23=2       $24=1000.0  $25=4000.0
$26=250     $27=10.000  $28=0.100   $29=0.0     $30=1000.000 $31=0.000
$32=0       $33=5000.0  $34=0.0     $35=0.0     $36=100.0   $37=0
$39=1       $40=1       $41=0       $42=2       $43=1       $44=3
$45=0       $46=0       $47=0       $56=5.0     $57=100.0   $58=-5.0
$59=500.0   $60=0       $61=0       $62=0       $63=3       $64=0
$65=0       $70=11
$100=80.00000   $101=80.00000   $102=250.00000  $103=4.44444
$110=20000.000  $111=20000.000  $112=500.000    $113=80000.000
$120=1500.000   $121=1500.000   $122=10.000     $123=6000.000
$130=455.000    $131=451.000    $132=200.000    $133=0.000
$300=grblHAL    $301=0          $302=10.10.10.2  $303=10.10.10.1
$304=255.255.255.0  $305=23     $307=80     $308=21     $341=0
$342=30.0   $343=25.0   $344=200.0  $345=200.0  $346=1  $370=0  $372=0
$376=1      $384=0      $392=4.0    $393=1.0    $394=0.0  $398=100
$481=0      $484=1      $485=0      $486=0      $534=0  $535=
$538=0      $539=0.0    $650=0      $673=0.0    $675=0  $676=15
$680=0      $700=0      $701=0
ok
```

Notes on the "before" dump:

- `$103=4.44444` steps per A unit x 4331.9664 motor deg per revolution =
  19,253 steps per bed revolution, matching the documented A calibration, so the
  A axis is in motor degrees as the converter assumes.
- `$133=0.000` - A has no travel limit, which is correct for a rotating axis.
- `$113=80000.000` - the setting under change.
- `$123=6000.000` - already equal to the converter's assumed A acceleration;
  no change needed unless the bed still stalls.

Commands to apply:

```text
$113=20000
$$
```

## Procedure

1. Record `$$` with the machine idle (the dump above).
2. Send `$113=20000`. Expect `ok`.
3. Send `$$` and confirm `$113=20000.000`, `$123=6000.000`, and that
   `$110`-`$112` / `$120`-`$122` are unchanged.
4. Power-cycle the controller and confirm the settings survive.
5. HOME and run `P100` to register the bed.
6. Mark test: draw a 5 mm reference line (MDI `M3`, `G4 P3`, jog, `M5`), note
   the DRO `A`, then run `G91 G1 A4331.9664 F20000` and
   `G91 G1 A-4331.9664 F20000` (one bed revolution out and back at the new
   limit, about 13 s each way), and draw the same line again. The marks must
   coincide.
7. Optional ratio check: plot `samples/gcode/theta-calibration.gcode` and read
   the circle/spiral closure per `WSW-20260930-021`.

## Results

**Settings change applied and persistent (2026-10-01).** After
`$113=20000` and a power cycle, `$$` reports `$113=20000.000` and
`$123=6000.000`. A 109-key comparison of the before and after dumps shows
exactly one difference:

```text
$113: 80000.000 -> 20000.000
```

No other setting moved, so the change is isolated to the A-axis maximum rate.
20000 motor deg/min is 333.3 motor deg/s = 27.7 bed deg/s; the retired 80000
was 1333.3 motor deg/s = 110.8 bed deg/s = 357.8 mm/s (21.5 m/min) of pen
surface speed at the 185 mm rim.

Cross-check from the dump: `$103 = 4.44444` steps per A unit x 4331.9664 motor
deg per bed revolution = 19,253 steps per bed revolution, matching the
documented A calibration.

**Mark test (the acceptance criterion): PENDING.** Draw a reference line, run
`G91 G1 A4331.9664 F20000` and `G91 G1 A-4331.9664 F20000`, redraw, and record
whether the marks coincide.

**Ratio check (`theta-calibration.gcode`): PENDING / optional.**

## Difficulties and corrective actions

- The value was already the only one that needed changing: `$123` was 6000
  motor deg/s^2, matching the converter's assumption, so it was left alone to
  keep the mark test to a single variable.
- Nothing else was touched; in particular `$103` (A steps per degree) was left
  at the calibrated value so the ratio question stays separate from the rate
  question.

## Conclusion

The A-axis maximum rate is now what the bed can hold, and it survives a reboot.
The change is recorded and isolated. This note becomes *verified* when the mark
test shows a full-revolution out-and-back returning the pen to its mark;
until then the drift fix rests on the software evidence in
`WSW-20261001-010` (no drawing move over one safe bed step, no bare `G0`
carrying bed rotation, and 1333 -> 333 motor deg/s worst-case demand in a
local reproduction of the reported print).
