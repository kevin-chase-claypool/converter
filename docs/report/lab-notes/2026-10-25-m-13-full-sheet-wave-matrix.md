# Lab Note: 2026-10-25 - Full-sheet CMYK wave matrix

## Objective

Determine whether the zero-anchored CMYK wave screen preserves visible tonal
frequency/depth and keeps adjacent rows separate at all four screen angles,
with both A parked and production Xtheta/Ytheta motion, in one black-pen
program on the already-mounted 14-inch sheet.

## Configuration

- Hardware revisions: current installed XY + rotating-bed machine and
  production integrated toolhead.
- Wiring/pin map: unchanged production wiring; no wiring or firmware change
  was made for this test.
- Firmware commit/build: unchanged installed production integrated build.
- grblHAL settings: unchanged production settings, including A-axis
  acceleration `$123=6000`.
- Converter settings/sample: commit `549dacb`;
  `samples/gcode/cmyk-wave-coupon.gcode`, SHA-256
  `6337A70EF6009299207375F39AC4DBBB689D145A4EF4526345BD962E44EDA36D`.
- Program settings: 16 patches, 234 x 142 mm matrix, 54 x 28 mm patches,
  C15/M75/Y0/K45 columns, 3.36 mm paper pitch, 0.8 mm black pen, `F700`,
  0.05 mm Path tolerance, compensation fingerprint `4c8270de8a74`.
- Instruments: overhead phone photograph; no scanner or caliper measurement.

## Code, commands, and configuration used

```text
Repository commit: 549dacb
Program: samples/gcode/cmyk-wave-coupon.gcode
SHA-256: 6337A70EF6009299207375F39AC4DBBB689D145A4EF4526345BD962E44EDA36D

python tools\check_gcode_motion.py samples\gcode\cmyk-wave-coupon.gcode --strict

ioSender: open the program once and press Cycle Start once.
```

The program contains one `M2` and no `M0` pause.

## Procedure

1. Keep the previously mounted 14-inch sheet taped in place.
2. Load the black 0.8 mm pen, matching the nominal yellow-pen width.
3. Run `samples/gcode/cmyk-wave-coupon.gcode` through ioSender with one Cycle
   Start; do not retape, re-register, pause, or swap files.
4. Photograph the completed sheet overhead, then inspect enlarged views of all
   four angle columns and paired wave rows.

## Results

- The single program completed all 16 patches: four screen angles by two wave
  modes in each of the upper parked and lower Xtheta/Ytheta matrices.
- No adjacent rows were visible connecting or crossing in the enlarged image.
- The zero-anchored patches showed clear changes in winding frequency and
  depth. Their paired equidistant controls retained the regular one-pitch row
  pattern.
- No gross patch displacement, missing angle column, or parked-versus-driven
  matrix mismatch was apparent at photo resolution.
- A few isolated dark specks and short end marks appeared in otherwise blank
  gaps. They did not connect neighboring rows and are treated as pen-start/end
  artifacts, not wave-row contact.
- The photo is oblique, so exact ink-edge separation was not measured.

Evidence:

- [Complete mounted sheet](assets/2026-10-25-m-13-full-sheet-wave-matrix.jpg)
- [Enlarged matrix](assets/2026-10-25-m-13-full-sheet-wave-matrix-zoom.jpg)

## Difficulties and corrective actions

- The original two-patch coupon covered only the 75-degree screen angle and
  could not test the full CMYK set. The single-run sixteen-patch matrix was
  generated in `WSW-20261024-014`; it retains all angles and both motion modes
  on the mounted sheet.
- A first implementation split the matrix into two files. That was rejected
  because the operator required one uninterrupted Cycle Start. Separate parked
  and motion plans are now combined behind one preamble and one program end.

## Interpretation

The black geometry diagnostic passes visual inspection for the reported
row-contact defect at all four screen angles and under both parked and
rotating-bed planning. This supports the zero-anchored generator and its
segment-level clearance pass. The photograph cannot prove sub-millimetre edge
clearance or predict yellow/magenta ink behavior.

## Decisions and next action

Do not spend another sheet on the black coupon. Proceed to one regenerated
yellow Ben1 layer at the production settings and inspect that layer before
printing magenta or black.
