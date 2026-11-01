---
id: WSW-20261101-006
date: 2026-11-01
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/kinematics.py
  - software/tests/test_contour_order.py
tags:
  - cmyk
  - wave-screen
  - contour-order
  - row-sweep
  - image-flip
  - 45-degree
  - striation
related:
  - WSW-20261101-003
  - 2026-11-01-m-13-cmyk-black-row-direction.md
---

# Correct rotated Wave row direction after the SVG Y flip

## Summary

Rows ascending and Rows descending now project row runs onto the final
paper-space row axis. The black CMYK screen at 45° no longer alternates
between fragments in an unpredictable order.

## Reason

The operator reported that descending row order materially improved the print
through cyan, magenta, and yellow, but the black pass still returned among
disconnected parts of a row badly enough that the operator stopped a
multi-hour print. Black is the 45° screen. Wave geometry is rotated before SVG
serialization, then `read_svg` mirrors Y when the normal flip-Y setting is
enabled. Row ordering used the pre-flip angle, so the projection was the
reflected axis rather than the actual path axis. At 45° the wrong projection is
nearly zero, making contour sort and reversal depend on tiny coordinate noise.

The stored earlier Jeep set (`2026-11-01 12:33:38`) records adjacent-order
`rows_ascending`, not the later descending trial. Its black G-code begins with
fragment IDs `4,3,1,2,6,5` and mixed physical directions instead of one ordered
sweep, independently confirming the defect.

## Implementation

`planned_contours()` negates `row_lock_screen_angle_deg` when `flip_y` is
enabled before calling `_source_order_contours()`. This reconstructs the row
axis in final paper coordinates while preserving the existing row grouping,
fragment ordering, and alternating serpentine direction.

## Verification

- The new 45°-rotated, Y-flipped regression failed before the fix with
  directions `+,+,+,+,+,−,+,+` instead of `+,+,−,−,+,+,−,−`.
- The regression now covers both `rows_ascending` and `rows_descending`.
- The focused contour-order, CMYK-tab, infill-bridging, and motion-check suites
  pass 125 tests.
- The complete converter suite passes 603 tests with one expected OpenGL-context
  skip.
- A fresh physical four-pass print has not yet been captured.

## Struggles and rejected approaches

The original row-order tests asserted contour IDs but used horizontal,
unrotated rows. That passed while the 45° mirrored case was unstable. Inferring
row bands from final Y coordinates was already rejected because Wave depth can
move a fragment across a naive band boundary; the existing source row ID stays
the authority.

## Risks and follow-up

The fix corrects ordering only after the existing SVG pipeline has applied the
same flip setting. Regenerate all four G-code files and restart an already-open
converter window so it cannot retain the old planner. A fresh print must confirm
that black now advances monotonically through each 45° row and must record the
elapsed-time penalty before row order becomes a default.

## Files

- `software/converter_core/kinematics.py`: applies the row-axis handedness after
  the SVG Y flip.
- `software/tests/test_contour_order.py`: locks 45° ascending and descending row
  direction after mirroring.
- `software/README.md`, `docs/testing/TEST_PLAN.md`, and
  `docs/project/ROADMAP.md`: current behavior and pending physical acceptance.
