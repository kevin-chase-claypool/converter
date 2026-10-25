# Lab Note: 2026-10-25 - Independent CMYK wave depth across pitch

## Objective

Determine why the latest yellow Ben1 wave screen was still visually
monotonous, verify whether the defect depends on Dot pitch, and prepare one
low-cost physical test that exercises every production CMYK screen angle at
three pitches without using another full 14-inch sheet.

## Configuration

- Hardware revisions: current installed XY + rotating-bed machine and
  production integrated toolhead; no hardware change was made.
- Wiring/pin map: unchanged production wiring.
- Firmware commit/build: unchanged installed production integrated build.
- grblHAL settings observed during the preceding investigations:
  `$113=30000` motor deg/min and `$123=6000` motor deg/s2.
- Failed print program:
  `samples/gcode/Ben1/IMG_0514-cmyk-yellow.gcode`, timestamp
  `2026-10-25 08:58:23`, SHA-256
  `2956E0C0C9186F32B65141858E8720ED45BF64156A1D4138DC51FEF4F28D10DD`.
- Source artwork: `C:\Users\jacks\Downloads\IMG_0514.JPG`, SHA-256
  `e3943aed851fd596fe38f783bb59ef16eca8a433425049aae0ee71fc11d85a45`.
- Failed-print recipe: Dot pitch `1.00 mm`, Artwork scale `280 %`, effective
  pitch `2.80 mm`, pen `0.80 mm`, Path tolerance `0.05 mm`, F700, central
  hold `60 mm`, Xtheta/Ytheta motion, and bed compensation enabled.
- Image controls used by the failed print: Auto levels on, saturation `115 %`,
  contrast `250 %`, brightness `40 %`, Ink gamma `3.00`, GCR `99 %`, and equal
  CMYK weights.
- The running converter PID `47340` started at `08:45:15`, before the
  uncommitted independent-row depth changes. Its loaded core could not contain
  that fix.
- Instruments: operator photograph
  `C:\Users\jacks\Downloads\wtf.jpg`; software inspection and deterministic
  unit/property checks.

## Code, commands, and configuration used

```text
Repository base: 6eecdaf
Failed yellow: SHA-256 2956E0C0C9186F32B65141858E8720ED45BF64156A1D4138DC51FEF4F28D10DD

python -m unittest -v software.tests.test_cmyk_tab
python -m unittest -v software.tests.test_cmyk_wave_coupon
python tools\check_gcode_motion.py samples\gcode\cmyk-wave-pitch-coupon.gcode --strict
python tools\make_cmyk_wave_coupon.py --multi-pitch
```

The regenerated Ben1 set is in `samples/gcode/Ben1/`; its version-2
`IMG_0514-cmyk-set.json` records all settings and hashes. The failed files were
preserved unchanged under `samples/gcode/Ben1/pre-independent-depth-2026-10-25/`.

## Procedure

1. Inspect the failed yellow photograph and compare its broad areas with the
   generated wave geometry.
2. Recreate the Ben1 luminance/screen path and count zero crossings per row.
3. Run the red regression at `2.80`, `3.36`, and `4.20 mm`; each pitch failed
   the frequency-depth criterion on the common-carrier implementation.
4. Replace the common carrier with independent row phase, monotone row
   projection, and the pitch-scaled pen-envelope bound.
5. Re-run real-image screening, generate all four Ben1 files, and apply the
   strict motion checker.
6. Build the single-program multi-pitch black coupon for the next physical
   check.

## Results

- The failed yellow print shows highly repetitive horizontal wave rows with
  little broad low/high-frequency variation across the portrait.
- The red loop proved pitch was not the cause. Before the change, both light
  and dark rows had exactly `100 / 83 / 66` zero crossings at
  `2.80 / 3.36 / 4.20 mm`. After the change, a dark row has at least `1.35x`
  the crossings of a light row at every pitch.
- The real Ben1 yellow geometry at `2.80 mm` had regular sampled-column gaps of
  `2.230-3.373 mm`. Long visible runs ranged from slow/flat behavior to 255
  crossings, at least an order of magnitude more frequency depth than the
  failed common carrier.
- All four regenerated Ben1 programs pass the strict motion checker:

| Ink | Drawing moves | Max bed step | Peak A rate | Strict result |
|---|---:|---:|---:|---|
| Cyan | 78,956 | 1.73 deg | 264.6 deg/s | Pass |
| Magenta | 106,758 | 5.96 deg | 268.6 deg/s | Pass |
| Yellow | 131,879 | 6.33 deg | 268.4 deg/s | Pass |
| Black | 121,617 | 6.77 deg | 267.8 deg/s | Pass |

Yellow's worst bounded path bow is `0.139 mm`; the checker permits the four
moves over the `0.05 mm` nominal tolerance when the existing subdivision cap
binds. No pen-up move contains a bare `G0` rotation.
- `tools\check_cmyk_set.py` reports all four programs inside the configured
  machine travel window.
- Every regenerated Ben1 file still carries
  `bed compensation 4c8270de8a74, coverage 171.450 mm, max 1.331 mm`.
- Regenerated yellow SHA-256:
  `915D7AAFB123AB105E9BB7EC70C4A0DF27303F877E7ED74E0CC4E23B05D785D3`.
- Multi-pitch black coupon:
  `samples/gcode/cmyk-wave-pitch-coupon.gcode`, SHA-256
  `DF1F281289215FE029496B9458E23C7D56EA744F97F7BE5CBFD92E922B12D9A8`.
  It contains 12 patches in one file, `45,743` drawing moves, one `M2`, and no
  `M0`. It passes strict motion checks with a `5.71 deg` maximum bed step,
  `269 motor deg/s` peak A rate, no pen-up rotation, and `0.108 mm` worst
  bounded path bow.
- Full converter discovery passes `532` tests with one expected
  OpenGL-context skip.
- No physical print of the regenerated geometry has been completed yet.

### 2026-10-25 11:01 restarted-generation check

- The refreshed converter process PID `22648` started at `10:55:23`. The four
  Ben1 files and manifest were saved at `11:01:08`, so the output was generated
  after the new converter loaded.
- The yellow file SHA-256 is
  `184F5736FEF1043FF22C66F8C83C1987B5465DDE0ED5E80E5FEA3EA3BE98A805`;
  the manifest records the same hash. It contains `141,895` drawing moves and
  declares the new `waves_zero`, effective `2.80 mm`, `1.05 mm` centerline
  clearance recipe with compensation `4c8270de8a74`.
- `check_gcode_motion.py --strict` passes: largest bed step `6.70 deg`,
  largest A rate `268.4 motor deg/s`, no pen-up rotation, and worst bounded
  path bow `0.153 mm`. Four moves exceed the nominal `0.05 mm` tolerance under
  the existing subdivision-cap exception. All four files remain inside the
  travel window.
- The matching intermediate SVG is
  `C:\Users\jacks\AppData\Local\Temp\theta_generator_tabs\cmyk-y-1792943809940-ed9efb.svg`.
  It contains `1,116` polylines and `360,535` sampled points. Regular-column
  gaps in the visible page measured `2.218-3.338 mm`, so the geometry is
  clearance-safe and does not reproduce the old close-row defect.
- The visual result still fails the depth criterion. Compared with the failed
  08:56 source SVG, median row amplitude fell from about `1.243 mm` to
  `0.298 mm` and peak amplitude from `1.257 mm` to `0.333 mm`. Frequency
  density increased from `0.235-0.329` to `0.667-0.796` crossings/mm.
- Side-by-side source rendering confirms the new result is mostly shallow,
  dense ripples rather than the intended combination of broad waves and tighter
  high-frequency detail. Do not print this yellow file yet.

### 2026-10-25 local amplitude-budget correction

- Red test one placed a small `12 x 4 px` hard-depth patch in one active band.
  The old global budget reduced untouched-row travel from `1.187` to `0.741`.
- Red test two placed a steep depth change entirely over blank paper. The old
  calculation reduced visible row travel from `1.715` to `0.565`.
- The real screen produced an exact projected floor of
  `0.7499999999999929` against the nominal `0.75`; strict comparison invoked
  the global damp-to-safe fallback despite a nearest real segment distance of
  `1.53 mm` on paper.
- The implementation now computes each row's slope budget independently,
  excludes transitions where either sample is blank, and allows `1e-9` for
  the exact band floor. Frequency gain is reduced from `2.0` to `1.0` so the
  safe rows retain visible height while light/dark frequency still differs.
- Real Ben1 yellow now passes its first clearance check with no global scale
  reduction. Peak-to-peak row height has `1.142 mm` median, `1.077 mm`
  first-quartile, and `1.354 mm` maximum, up from roughly `0.65 mm` median in
  the over-damped 11:01 source. Side-by-side rendering now shows varied
  shallow/deep rows instead of a field of uniform tiny ripples.
- All four angles pass their first clearance check:

| Ink | Marks | Source points |
|---|---:|---:|
| C15 | 1,840 | 151,770 |
| M75 | 1,859 | 205,174 |
| Y0 | 1,115 | 240,407 |
| K45 | 1,792 | 222,106 |

- The regenerated Ben1 set was saved at `11:20:19`. Yellow SHA-256 is
  `216152CD5EAE26206FA76CC092F109E481D4562664B056C9D6F51258CE943766`.
  It has `88,467` drawing moves and passes strict motion checks at a
  `5.26 deg` largest bed step and `269 motor deg/s` peak A rate.
- All four regenerated files pass strict motion and travel-window checks with
  compensation `4c8270de8a74` active. The failed 11:01 set is preserved under
  `samples/gcode/Ben1/pre-local-budget-2026-10-25-1101/`.
- Full converter discovery passes `535` tests with one expected
  OpenGL-context skip.

### 2026-10-25 11:33 application-saved set

- The user regenerated the four-file set from converter PID `37112`, which
  started at `11:29:04` with the corrected local-budget code. The files were
  saved at `11:33:14`.
- The version-2 manifest records `waves_zero`, frequency gain `1.0`, effective
  pitch `2.80 mm`, `1.05 mm` centerline clearance, F700, rotating-bed motion,
  and bed compensation `4c8270de8a74`.
- The application's yellow intermediate SVG SHA-256 is
  `ABF173235ABE0400D269205D8EED148BA1593BF284384577C9E9C7C22C5087E7`,
  byte-identical to the local-budget generation. It contains 1,115 polylines
  and 240,407 sampled points.
- Independent SVG measurement finds 72 visible wave rows with `1.142 mm`
  median and `1.354 mm` maximum peak-to-peak height. Crossing density spans
  `0.428-0.584` per millimetre; visual comparison shows varied shallow/deep
  rows rather than the former uniform tiny ripples.
- Application-saved yellow G-code SHA-256 is
  `EFD6150609F31D3EA09175B62D00E0B8DBDA5808443883E666EC3DF5D3BAAFB1`
  and the manifest hash agrees. It contains `94,601` drawing moves and passes
  strict motion checks with a `5.36 deg` maximum bed step,
  `268.8 motor deg/s` peak A rate, no pen-up rotation, and `0.096 mm` worst
  bounded path bow. All four files remain inside the travel window.
- This is a software/preview pass. No yellow ink was used for this check.

### 2026-10-25 physical yellow photo inspection

- The operator supplied an overhead photograph of the completed yellow layer:
  [original photograph](assets/2026-10-25-m-13-local-budget-yellow-photo.jpg).
- The saved G-code was decoded back to bed space by reversing each A angle,
  the measured 12.03324 motor-degrees per bed-degree ratio, and compensation
  profile `4c8270de8a74`.
- The decoded geometry contains 94,601 pen-down points in 567 runs over 115
  visible row bands. Its bed-space extent is X `-171.429..171.426 mm` and Y
  `-154.159..170.665 mm`.
- A visual side-by-side comparison
  ([decoded G-code and rotated photograph](assets/2026-10-25-m-13-local-budget-yellow-code-vs-photo.png))
  places the large white regions, branch-shaped gaps, isolated arcs, and outer
  yellow fields in both images. They are commanded by the yellow separation,
  not missing motion blocks introduced by bed rotation.
- Independent clearance measurement on the decoded G-code finds a minimum
  centerline separation of `1.649 mm`; no adjacent pair falls below the
  required `1.05 mm` pen envelope. The minimum same-column visible gap is
  `2.096 mm`.
- The photograph is oblique and cannot resolve sub-millimetre ink-edge contact.
  It therefore neither confirms the reported touching rows nor proves the
  machine follows perfectly; it does show that the large-scale gaps are not a
  bed-synchronization artifact.
- If rows physically touch, the next evidence must be a straight-down close-up
  of that specific area, with its position relative to the registered center,
  plus the same yellow path in XY-only mode. That will separate ink spread or
  gantry motion from residual A following error.

## Difficulties and corrective actions

- The failed print's effective `2.80 mm` pitch differed from the black
  coupon's `3.36 mm`, so a coupon pass did not cover the actual failing scale.
- The selected zero-anchored mode initially retained independent row amplitude
  but supplied all rows with one common frequency carrier. The common carrier
  appeared safe while suppressing the defining low/high-frequency depth.
- Simply letting rows move independently restored depth but could violate the
  physical pen envelope on steep flanks. The final implementation combines row
  ordering, a slope-aware amplitude bound, and exact segment verification.
- The failed outputs are retained because the regenerated files are not a
  substitute for a physical pass.
- The first independent-row build preserved clearance by globally limiting
  wave slope. On the cropped Ben1 region this reduced amplitude about fourfold
  and made the visual pattern flatter despite increasing frequency. The next
  attempt initially allocated the clearance budget by row, but blank-region
  depth changes could still flatten a row's emitted segments.
- The final correction considers only adjacent active samples and accepts an
  exact projected band floor within numerical tolerance. This prevents both a
  blank-paper depth edge and floating-point noise from activating the global
  fallback.

## Interpretation

The source geometry for the latest failed print could not have contained the
independent-row fix: both the file and converter process predated it. The
common-carrier law also explains why changing pitch or machine acceleration had
no effect and why all CMYK layers failed together. The new geometry changes the
screen itself before motion planning while retaining compensation.

The software evidence now covers source depth, first-attempt clearance, motion,
travel, and reproducibility. The corrected yellow preview has visible mixed
wave heights instead of the over-damped uniform ripples. Physical ink-edge
clearance and the final visual quality remain unproven until the pitch coupon
and yellow layer are printed.

## Decisions and next action

1. The restarted converter and the `11:33` yellow preview are software-verified.
   Keep the preserved `11:01` file only as failed evidence.
2. Before another full sheet, run
   `samples/gcode/cmyk-wave-pitch-coupon.gcode` in ioSender with the black
   `0.8 mm` pen. Use ordinary paper, tape it once, issue no pause, and press
   Cycle Start once.
3. Set ioSender feed override to `100 %`; F700 is already in the file. Do not
   change `$123` for this geometry test. Record the active A acceleration in the
   result so the run remains traceable.
4. Inspect all twelve patches. The three horizontal bands are `2.80`, `3.36`,
   and `4.20 mm` pitch; each contains C15/M75/Y0/K45 left to right. Pass means
   visible low/high-frequency depth within rows, no neighboring strokes
   touching, and no pitch-dependent collision pattern.
5. If the coupon fails, stop and photograph it; do not print yellow. If it
   passes, inspect the regenerated yellow preview, then print only
   `samples/gcode/Ben1/IMG_0514-cmyk-yellow.gcode` before any other ink.

Evidence:

- `WSW-20261025-002`
- Replaced failed set: `samples/gcode/Ben1/IMG_0514-cmyk-set.json`
- Preserved prior set:
  `samples/gcode/Ben1/pre-independent-depth-2026-10-25/`
- `docs/testing/TEST_PLAN.md` test `M-13`
