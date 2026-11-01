---
id: WSW-20261101-001
date: 2026-11-01
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - legacy
  - diagnostic
  - bed-compensation
  - dense-v3
related:
  - WSW-20261031-001
  - ADR-009
---

# Add a legacy Wave diagnostic on the current compensation mesh

## Summary

The CMYK screen selector now includes a temporary legacy Wave mode that
recreates the old tone-varying row geometry without reverting the active bed
compensation profile.

## Reason

The clean Ben2 reference print used `waves_zero`, where each row's amplitude
followed its own locally smoothed tone. Current production promotes legacy
Wave requests to `waves_even`, which applies one shared waveform to every row.
Testing whether that geometry change caused the later striation requires
comparing it against the current centered dense-v3 mesh rather than an older
calibration.

## Implementation

- Added **Wave screen - legacy phase-locked depth (diagnostic)** as an explicit
  `waves_zero` selector entry.
- The diagnostic passes `allow_variable_wave_spacing=True`; ordinary stored
  `waves` and `waves_zero` values still promote to production
  `waves_even` geometry.
- The Machine-tab compensation path remains the current selection and defaults
  to `bed-error-compensation-2026-10-29-dense-v3-centered.json` with
  fingerprint `18bfb4ed1c33`.
- Legacy Wave disables both the equidistant spacing guard and carrier-frequency
  modulation, so it applies the selected profile's raw two-dimensional
  correction. Its manifest records `raw_unconstrained` compensation.

## Verification

- The selector exposes both the production and diagnostic modes.
- All four ink layers build in the legacy mode.
- Instrumented layer generation records `allow_variable_wave_spacing=True`,
  `style=waves_zero`, and no carrier-frequency variation.
- A planned yellow layer uses profile fingerprint `18bfb4ed1c33` and is not a
  row-locked compensation profile.
- The focused selector, legacy-mode, four-layer, production row-lock, and set
  manifest tests pass.
- The full converter suite passes `591` tests with one expected OpenGL-context
  skip.

## Struggles and rejected approaches

Reverting the whole converter was rejected because it would also reset the
default bed mesh and unrelated fixes. Converting the legacy style internally
without changing the UI was rejected because it would leave no explicit
warning or traceable manifest value for the non-production geometry.

## Risks and follow-up

The legacy mode intentionally permits unequal adjacent row spacing because
tone controls row-specific amplitude. Use it only for a matched A/B
diagnostic. Keep the current dense-v3 profile, use `XY only` for the first
comparison, and print the same crop through both modes before changing the
production algorithm.

## Files

- `software/generator_tabs/cmyk_tab.py`: diagnostic selector entry and opt-in
  to the existing legacy Wave implementation.
- `software/tests/test_cmyk_tab.py`: selector, current-mesh, raw-compensation,
  and layer-generation regressions.
- `software/README.md`: operator behavior and warnings.
- `docs/testing/TEST_PLAN.md`: old-Wave/new-mesh comparison procedure.
- `docs/project/ROADMAP.md`: current striation-investigation status.
- `docs/project/ENGINEERING_LOG.md`: implementation event.
