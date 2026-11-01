# Lab Note: 2026-11-01 - M-13 CMYK row order through the 45° black screen

## Objective

Determine whether ascending or descending Wave-row order prevents the planner
from returning unpredictably within a row band, and identify why the black
pass still failed after the other three inks improved.

## Configuration

- Hardware revisions: N20 toolhead actuator with replacement motor; the
  replacement motor pinion was reported faulty and is a separate mechanical
  issue from row ordering.
- Wiring/pin map: TBD for this print; no wiring change was made during the row
  comparison.
- Firmware commit/build: not captured for the physical print.
- grblHAL settings: not captured for the physical print.
- Converter settings/sample: Jeep image
  `IMG_20200613_062031.jpg`, four CMYK passes, `XY only (bed parked, precise)`,
  200 mm page, nominal 0.50 mm source pitch at 380% artwork scale, 2.66 mm
  effective pitch, pen width 0.80 mm, feed 700 mm/min, travel 3000 mm/min.
- Screens: C 15°, M 75°, Y 0°, K 45°.
- Instruments: operator visual inspection; no calibrated image capture was
  recorded.

The stored earlier generated set is:

```text
samples/gcode/jeepbeach/IMG_20200613_062031-cmyk-set.json
created: 2026-11-01T12:33:38
screen.contour_order: rows_ascending
Y sha256: a29b2f5072bba24cbe88a62b6a981f4651e69d23a9d156d5b9280cf9753f89e7
K sha256: 5fc9f7a768915f26c65ca180c8938e5a530fb753768b39aef02b0049fb20fb12
```

The operator later changed row order to descending, observed a significant
quality improvement, and reported the current four-ink print remained good
until black. The later descending artifacts were not saved back to this set
directory, so the manifest above identifies only the earlier ascending run.

## Code, commands, and configuration used

The diagnosis was run against base commit `aa66c54` plus the row-angle fix in
this session:

```powershell
py -3 -m unittest software.tests.test_contour_order.ContourOrderTests.test_rotated_flipped_rows_keep_their_serpentine_direction -v
py -3 -m unittest discover -s software\tests
```

The failing 45° fixture represented eight Wave fragments in four rows after
the normal SVG Y-axis flip. Before the fix, path directions were:

```text
+ + + + + − + +
```

The required serpentine directions are:

```text
+ + − − + + − −
```

## Procedure

1. Print successive cyan, magenta, yellow, and black layers from the same CMYK
   recipe without adjusting the sheet or artwork placement.
2. Change Wave row order to descending for the later comparison.
3. Record at which ink visible row-return behavior begins.
4. Inspect the stored black G-code and reproduce its rotated row geometry in
   the row-ordering regression.
5. Correct the final paper-space row axis and rerun focused and complete
   converter tests.

## Results

The operator reported that descending row order significantly improved print
quality. Cyan, magenta, and yellow were acceptable in the later trial. Black,
the 45° screen, still printed in seemingly random locations within each row
instead of continuing monotonically through the serpentine sweep. The failure
was severe enough that the operator stopped the multi-hour print.

The earlier stored black G-code begins with contour IDs `4,3,1,2,6,5`.
Projecting those paths on the physical 45° paper axis gives mixed directions
rather than the intended alternating row sweep. This reproduces the operator's
observation without relying on a planner-performance hypothesis.

The new angle-specific regression failed before the fix and now passes for
both ascending and descending modes. The complete converter suite passes 603
tests with one expected OpenGL-context skip.

## Difficulties and corrective actions

- The first row-order tests used horizontal rows, so they proved row grouping
  but not row direction after `flip_y`. The corrective test includes the 15°,
  45°, and 75° class of transformation through a representative 45° case.
- An earlier open converter window can retain old planner code after a source
  change. The next run must start a fresh application instance and regenerate
  every ink file.
- A gummed toolhead motor and faulty replacement pinion caused separate P115
  faults. Those are not evidence for or against row-order behavior.

## Interpretation

The clean CMY result and black-only failure localize this defect to contour
ordering for the rotated 45° screen, not to the XY planner, bed motion, P115,
or motor mechanics. Blank image areas still require pen lifts, but each
disconnected run should now advance along its row instead of jumping backward
or cycling through unordered fragments.

## Decisions and next action

Keep row order opt-in until the corrected build completes a fresh four-pass
print. Regenerate the Jeep set after restarting the converter, verify the black
contour sequence advances monotonically within each 45° row, then record print
quality and total elapsed time. See `WSW-20261101-006`.
