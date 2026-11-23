# Lab Note: 2026-11-22 - CMYK shared row-lock translation software geometry

## Objective

Determine whether the four CMYK row-lock projections keep one systematic
final-machine XY translation after the common-domain normalization, without
changing adjacent-row spacing, and define the remaining physical comparison.

This is a software-geometry note. No controller motion or paper comparison was
performed in this run.

## Configuration

- Hardware revisions: not used.
- Wiring/pin map: not used.
- Firmware commit/build: not used.
- grblHAL settings: not used.
- Converter profile: `f85ec410dbac`, 180.000 mm coverage.
- Screen angles: cyan 15 degrees, magenta 75 degrees, yellow 0 degrees, black
  45 degrees.
- Common translation domain: 65 by 65 bed-frame samples per axis, clipped to
  the compensation coverage disk.
- Instruments: software coordinate inspection only.

## Code, commands, and configuration used

Focused emission regression:

```powershell
python software\tests\test_bed_compensation.py `
  BedCompensationPlannerIntegrationTests.test_cmyk_row_lock_emits_one_shared_translation -v
```

Focused rotating-bed row check:

```powershell
python software\tests\test_wave_x_theta_rows.py -v
```

This automation session invoked the same commands through
`C:\Users\jacks\AppData\Local\Programs\Python\Python313\python.exe` because
the inherited `python` PATH entry resolved to an inaccessible zero-length
`C:\Windows\system32\python` alias.

Rendered-program configuration for both tests:

```text
theta_mode: fixed for centroid emission; optimized for Xθ/Yθ row quality
theta_center_hold_diameter_mm: 0.0
bed_compensation_path: samples/gcode/bed-error-compensation-2026-11-01-dense-v3-360mm-reach-extrapolated.json
row_locked_compensation: true
row_lock_screen_angle_deg: 15, 75, 0, 45
common_translation_mm: 0.0, 0.0
```

## Procedure

1. Build the same dense paper-coordinate point set for all four inks.
2. Plan and emit G-code through the normal contour planner and G-code writer
   with each ink's screen angle and the prepared shared projection.
3. Decode pen-down final machine X/Y and compare the set centroids.
4. Use the fixed-bed emission point set for final XY translation, then run the
   Xθ/Yθ row-pitch audit for both row orders and all four screen angles.
5. Compare raw-profile output and reversed angle ordering.
6. Measure the pointwise difference left between each normalized field and
   yellow; do not reinterpret this as physical overlay evidence.

## Results

The first emission regression failed on the pre-fix code. Cyan's mean machine
coordinate differed from yellow's by `0.059483 mm` over the identical point
set.

After the fix, the same test passes with every CMYK centroid within
`0.0002 mm`; the residual is consistent with three-decimal G-code
quantization. The direct normalized projection means are below `3e-15 mm` at
every measured bed angle.

Software correction centroids from four `(+/-75, +/-75) mm` registration
crosses are:

| Ink | Before normalization mm | After normalization mm |
|---|---|---|
| C | `(0.209524, 0.098000)` | `(0.029121, -0.042789)` |
| M | `(-0.043377, 0.231899)` | `(-0.007348, 0.006409)` |
| Y | `(0.198440, 0.075544)` | `(-0.012840, -0.014403)` |
| K | `(0.103333, 0.236177)` | `(0.019470, 0.024378)` |

The compensated Xθ/Yθ row test passes at all four screen angles and both row
orders. Final adjacent-row spread remains below the existing `0.005 mm` bound.
Raw shared-profile programs remain identical across the four screen-angle
settings, and reversed angle input produces the same projection fingerprints.

The normalized fields still contain local differences. Relative to yellow over
the common domain, the software pointwise residual is:

| Pair | RMS mm | Maximum mm |
|---|---:|---:|
| C - Y | `0.125914` | `0.443952` |
| M - Y | `0.328551` | `0.753089` |
| K - Y | `0.219316` | `0.533614` |

## Difficulties and corrective actions

The first proposed green threshold of `0.000001 mm` was below the exporter's
coordinate quantization. The test emitted three-decimal machine coordinates,
so absolute centroid agreement can only be asserted at the quantization scale.
The regression uses `0.0002 mm`, over 295 times narrower than the reproduced
pre-fix failure.

Using the pre-fix test grid directly would not have exercised the same domain
used to calculate the normalization. The final test builds the projection set
once and uses the deterministic common domain, avoiding a false assertion over
an unrelated point distribution.

## Interpretation

The cross-channel systematic translation bug is removed in software while the
row-locked along-row correction and exact row-pitch invariant remain. The
remaining pointwise variation is a local overlay limitation, not a shared
translation that this milestone can remove.

## Decisions and next action

See ADR-009 and `WSW-20261122-001`. Generate a fresh CMYK set with corner
crosses in a new converter process, then perform one HOME + REGISTER and run
the four files on a fixed sheet without re-registration. Record:

- all four cross coordinates after one physical run;
- the old-to-normalized centroid change;
- row spacing from the emitted and printed set;
- visible local distortion at the corners and field interior.

Do not promote this note to physical verification evidence until that run is
complete.
