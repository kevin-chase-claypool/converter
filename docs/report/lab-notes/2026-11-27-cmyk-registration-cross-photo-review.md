# Lab Note: 2026-11-27 - CMYK registration cross photo review

## Objective

Review physical four-ink registration after enabling the named corner crosses
and determine whether the previous whole-program offset remains.

## Evidence

Four close-up photographs were supplied, one per corner:

| Corner | Evidence |
|---|---|
| NE | [`corner-ne.png`](assets/2026-11-27-cmyk-registration/corner-ne.png) |
| SE | [`corner-se.png`](assets/2026-11-27-cmyk-registration/corner-se.png) |
| SW | [`corner-sw.png`](assets/2026-11-27-cmyk-registration/corner-sw.png) |
| NW | [`corner-nw.png`](assets/2026-11-27-cmyk-registration/corner-nw.png) |
| Combined review | [`registration-review.png`](assets/2026-11-27-cmyk-registration/registration-review.png) |

The combined review is a reproduction artifact made from the four originals.
The source PNG dimensions are `420 x 413` NE, `202 x 196` SE, `247 x 209` SW,
and `296 x 281` NW.

No camera model, focal length, object distance, page size, or calibration
target was supplied. Each image also uses a different crop and camera
orientation. The photos therefore support a gross physical review, not a
calibrated pointwise residual fit.

SHA-256:

- `corner-ne.png`: `9629FC7ABE4ADBDED03CA883E81F0373B395EBED9404B7A97B070FA9C30236E0`
- `corner-se.png`: `BBA7C6B74474803ABAC0C90815A120F5500445A62AB78E6366FE5C0C3E482552`
- `corner-sw.png`: `D15451554829A02064A34174715377478050C270D1820970AC78CEB2134FD32F`
- `corner-nw.png`: `78EEF8257170E471A47AC12D8D6076E0332D29CD84F7B880C0A7988EE29C582E`
- `registration-review.png`: `8BCA4EFF68DCBD6E4FB3D511488A741B03D8EE5E9B850D0F381EF706503D4AFE`

## Procedure

1. Compare the cyan, magenta, yellow, and black stroke centres at each corner.
2. Use the printed black cross span as the local image-scale reference.
3. Compare color-centre separation as a fraction of that span, then estimate
   millimetres assuming the current maximum cross span of `10 mm`.
4. Inspect all four corners for a common large translation or obvious rotation.

This is a manual/photo review. A grayscale luma threshold identified the black
cross centrelines; color-center estimates used the visible opposing-color
fringes. Ink spread and black overprinting make the color centers less precise
than the black skeleton.

## Results

All four corners contain a single overprinted cross. No color is displaced by
the previously observed approximately `10 mm` whole-program offset.

| Corner | Approximate colored-centre separation from black | Observation |
|---|---:|---|
| NE | 5-9 % of black span | Magenta/yellow horizontal fringe is above the black arm; cyan is partly visible at the left end. |
| SE | 4-5 % | Closest to coincident; colored fringe is mostly symmetric around the black cross. |
| SW | 5-7 % | Small opposing cyan/magenta fringe around a nearly centered black cross. |
| NW | 6-9 % | Largest visible colored fringe; magenta/cyan sit above and right of the black center in this image orientation. |

If the black cross span is `10 mm`, these rough center separations correspond
to approximately `0.4-0.9 mm`. The camera and ink-edge uncertainty is too large
for a tighter claim.

The direction of the apparent offset changes between photographs. Because the
camera orientation changed, these images cannot determine whether that is a
real page-frame translation/rotation, local bed error, or simply rotated image
axes.

## Interpretation

The physical result is grossly registered: every corner shows all four inks
within roughly one pen width, and the original large inter-program shift is
gone.

This does not satisfy the `0.10 mm` software registration threshold as a
physical measurement, nor does it establish a calibrated four-corner RMS or
maximum. It is consistent with a sub-millimeter physical residual from machine
registration, bed compensation, pen-tip differences, and ink spread.

SE is the closest. NW has the largest visible color separation in these crops;
NE and SW are intermediate.

## Decisions and next action

Do not make another waveform or registration translation change from these
close-ups alone. The next useful evidence is one overhead photograph containing
all four crosses and a known paper dimension or scale reference, after one
`G65 P113` and without changing G54 or the sheet between colors.

Record whether the run used **XY only** or **Xθ/Yθ**. If the next calibrated
measurement shows a common translation, treat it as a frame/pen issue; if the
offset changes sign or grows with radius, treat it as rotation, scale, or local
bed error rather than another global translation.

## Related records

- Registration implementation:
  [`WSW-20261127-001`](../../changes/windows-software/2026/2026-11-27-cmyk-gcode-registration-gate.md)
- Fit/preview follow-up:
  [`WSW-20261127-002`](../../changes/windows-software/2026/2026-11-27-cmyk-preview-registration-crosses.md)
- Decision:
  [`ADR-013`](../../decisions/ADR-013-gcode-registration-gate.md)
