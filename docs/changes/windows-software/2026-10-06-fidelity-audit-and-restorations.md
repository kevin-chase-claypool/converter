---
id: WSW-20261006-020
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs
tags:
  - generators
  - documentation
  - fidelity
related:
  - docs/research/2026-10-06-generator-tab-fidelity-audit.md
---

# Generator fidelity audit, restored options, and attribution corrections

## Summary

Every generated tab was compared option-by-option against its upstream source.
The audit found real omissions. This change restores the two cheapest gaps
(Line Draw **Simplify** and **Resolution**, Postcard **Message**), corrects two
overstated attributions (Flow Field, Snowflake), and records the larger gaps
as roadmap work.

## Reason

The owner noticed the ports looked simplified and asked to ensure options were
not removed. The audit confirmed simplifications in every ported tab.

## Implementation

- `line_draw_tab.py`: `resolution_px` (200-1400) and `simplify_px` (0.1-3.0)
  replace the hardcoded 900 px cap and 0.75 px Douglas-Peucker epsilon.
- `postcard_tab.py`: a **Message** text block in the left column, drawn with
  the shared Hershey layout like the caption and address.
- `flow_field_tab.py`, `flow_field_NOTICE.md`: wording now says the tab adapts
  the streamline placement method; the upstream formula field is not ported.
- `snowflake_tab.py`, `snowflake_NOTICE.md`: wording now says the tab is an
  independent dendritic generator inspired by the upstream art; the upstream
  mesoscopic lattice simulation is not reproduced.
- `software/tests/test_line_draw_tab.py`,
  `software/tests/test_postcard_tab.py`: coverage for the restored options.

## Verification

- `python -m unittest discover -s software\tests -p "test_line_draw_tab.py" -v`
  -> 5 tests pass, including resolution/simplify.
- `... -p "test_postcard_tab.py" -v` -> 6 tests pass, including message text.
- Full suite: `python -m unittest discover -s software\tests` -> 263 tests
  pass.
- The full comparison table is in
  `docs/research/2026-10-06-generator-tab-fidelity-audit.md`.

## Struggles and rejected approaches

- Porting every upstream option in this batch was rejected: 3D CSG/primitives,
  the physical harmonograph model, and the snowflake lattice simulation are
  each large features, and the multi-pen colour/layer options need a
  multi-pen workflow first.

## Risks and follow-up

- The roadmap lists the remaining gaps with acceptance criteria; the audit note
  is the source of truth for what is still simplified.

## Files

- `docs/research/2026-10-06-generator-tab-fidelity-audit.md`: audit table.
- `software/generator_tabs/line_draw_tab.py`: restored controls.
- `software/generator_tabs/postcard_tab.py`: message block.
- `software/generator_tabs/flow_field_*`, `snowflake_*`: attribution wording.
- `software/tests/test_line_draw_tab.py`, `test_postcard_tab.py`: coverage.
