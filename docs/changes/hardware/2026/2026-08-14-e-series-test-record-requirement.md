---
id: HW-20260814-001
date: 2026-08-14
category: hardware
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - docs/testing/TEST_PLAN.md
  - docs/report/LAB_NOTE_TEMPLATE.md
tags:
  - verification
  - lab-notes
  - test-process
related:
  - docs/project/ENGINEERING_LOG.md
---

# Require complete E-series test records

## Summary

Every E-series electrical-characterization test must now preserve how it was
performed, the evidence obtained, difficulties encountered, corrective work,
and the repeat result supporting a pass.

## Reason

The project owner requested reproducible records rather than pass/fail-only
test summaries, especially when a repair or configuration correction was
needed to obtain the result.

## Implementation

The test plan requires a dated lab note for every E-series attempt. The lab-note
template includes dedicated code/configuration and difficulties-and-corrective-
actions sections, and the lab-notes guide specifies the minimum content of each
E-series record. When code or commands are used, the exact version is embedded
in a fenced code block rather than referenced only by filename.

## Verification

- `python tools/docs_index.py --write`
- `python tools/docs_index.py --check`

## Struggles and rejected approaches

Earlier E-series notes could summarize a successful measurement without a
consistent place to record the intermittent connection, failed step, and repair
that enabled it. A pass/fail-only record was rejected as insufficient.

## Risks and follow-up

Existing historical notes are not retroactively rewritten unless they are
revisited. Apply this requirement to every future E-series test attempt.

## Files

- `docs/testing/TEST_PLAN.md`: mandatory E-series record content.
- `docs/report/LAB_NOTE_TEMPLATE.md`: exact code/configuration and recovery/evidence sections.
- `docs/report/lab-notes/README.md`: E-series lab-note requirements.
- `docs/project/ENGINEERING_LOG.md`: durable decision record.
