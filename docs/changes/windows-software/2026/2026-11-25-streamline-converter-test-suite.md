---
id: WSW-20261125-001
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/tests
  - software/README.md
tags:
  - tests
  - performance
  - context-window
  - cmyk
  - unittest
  - maintainability
related:
  - WSW-20261124-006
---

# Split and streamline the converter test suite

## Summary

The 4,389-line CMYK test module is now seven focused modules, and repeated
expensive Qt and generated-G-code setup is either cached or exercised through
subtests. The discovery suite reports 682 cases instead of 690 because eight
fixture-heavy tests were folded into three methods; every original assertion
remains.

## Reason

`test_cmyk_tab.py` contained 147 tests across separation, image processing,
screen geometry, Wave planning, and Qt UI behavior. Any agent or maintainer
working on one concern had to load the entire file, and the module accounted
for roughly 29% of all test source lines.

The slowest tests also rebuilt deterministic outputs unnecessarily:

- `test_wave_x_theta_rows` screened and serialized the same four angles inside
  every compensated/order permutation.
- The CMYK Wave coupon tests rebuilt the same coupon twice.
- Four typed-number tests repeated identical Qt window construction.
- Motif selection, source-size, and sidebar checks repeated equivalent windows
  for assertions on the same object.

## Implementation

- Split the former CMYK module into:
  - `test_cmyk_separation.py` (10 tests)
  - `test_cmyk_edge_flow.py` (14)
  - `test_cmyk_photo.py` (17)
  - `test_cmyk_screen_styles.py` (11)
  - `test_cmyk_wave.py` (22)
  - `test_cmyk_contract.py` (5)
  - `test_cmyk_tab.py` (68 Qt/UI tests)
- The split preserves all 147 original CMYK test method names exactly; only the
  containing module and, for screening groups, class name changed.
- Cached the deterministic CMYK Wave coupon result at class scope.
- Cached the four angle-specific Wave SVG documents before testing compensated
  and ordering permutations, and vectorized the row-gap sampler with `numpy`.
- Folded four typed-number scenarios, three motif-selection scenarios, two
  source-size checks, and three sidebar checks into subtests. The assertion
  count and labels remain visible on failure.
- Documented quiet targeted and full-suite commands in `software/README.md`.
  `unittest -b` was measured and rejected: buffering the full suite took
  `185.1 s`, versus `147.4 s` without it.

## Verification

- A source comparison against the previous `test_cmyk_tab.py` found `147` old
  CMYK test method names and `147` new names, with no missing or added names.
- All seven CMYK modules pass `147` tests.
- The complete converter suite passes `682` tests with one expected
  OpenGL-context skip.
- The angle-pitch regression fell from an instrumented `15.7 s` to `9.7 s`
  while retaining all compensation, row-order, angle, contour-order, G-code,
  and decoded-pitch assertions.
- The four heavily reused preview fixture classes fell from an instrumented
  aggregate `53.2 s` to `20.6 s` while retaining their state, persistence,
  sizing, and sidebar checks.
- The complete unbuffered suite completed in `147.4 s`, compared with `148.6 s`
  for the previous 690-case suite. The primary gain is reduced source and
  targeted-run overhead rather than a large change in full-suite wall time.
- The largest test module is now 1,706 lines instead of 4,389. Focused CMYK
  modules range from 108 to 1,069 lines.

## Struggles and rejected approaches

Splitting alone does not make the complete run faster; it reduces the source a
maintainer or agent must load for a targeted change. Total wall time still
depends heavily on Qt startup and the large bed-compensation/Wave planning
tests, so isolated runtimes can vary between workstations and sessions.

Keeping all duplicate setup in separate test methods was rejected for the four
fixed fixtures because it repeated identical expensive construction. Merging
unrelated behavior into broad tests was also avoided; only assertions sharing
the same fixture were combined.

## Risks and follow-up

Commands that named the old `test_cmyk_tab.ScreeningTests` class no longer work.
Historical change notes intentionally retain their old test commands. Current
instructions list the new modules and use quiet discovery.

The complete suite still contains 15,000+ test lines. Repeated generator-tab
contract methods remain because each tab has a different fixture and extracting
a common callback protocol would add more indirection than it removes.

## Files

- `software/tests/test_cmyk_tab.py`: UI and save/manifest coverage only.
- `software/tests/test_cmyk_separation.py`: separation and image metadata.
- `software/tests/test_cmyk_edge_flow.py`: Edge-flow screening.
- `software/tests/test_cmyk_photo.py`: photo curves and Auto behavior.
- `software/tests/test_cmyk_screen_styles.py`: non-Wave screen styles.
- `software/tests/test_cmyk_wave.py`: Wave geometry and clearance.
- `software/tests/test_cmyk_contract.py`: SVG and cost contracts.
- `software/tests/test_cmyk_wave_coupon.py`: class-scoped generated coupon.
- `software/tests/test_wave_x_theta_rows.py`: shared angle fixtures and
  vectorized gap sampling.
- `software/tests/test_preview_view.py`: shared-fixture subtests.
- `software/README.md`: targeted and buffered test commands.
- `docs/project/ENGINEERING_LOG.md`: chronological refactor and verification.
