---
id: HW-20260830-002
date: 2026-08-30
category: hardware
affected_categories:
  - hardware
status: planned
components:
  - docs/testing/RECOMMENDED_TEST_SEQUENCE.md
tags:
  - toolhead
  - testing
  - safety
  - preload
related:
  - HW-20260830-001
---

# Add Toolhead Test Stop/Go Rules

## Summary

Added explicit pass/proceed and fail-or-partial/stop rules to the recommended
toolhead test order.

## Reason

The prior sequence showed dependencies but did not state that a partial or
failed result blocks its dependent test.

## Implementation

The sequence now defines a global evidence rule and stage-specific decisions
for the preload geometry, motor direction, loaded electrical capability,
sensor characterization, motor/preload envelope, and closed-loop/fault tests.
Detailed quantitative pass conditions remain authoritative in
`docs/testing/TEST_PLAN.md`.

## Verification

- `python tools/docs_index.py --write` — pending.
- `python tools/docs_index.py --check` — pending.
- No physical test was performed or reclassified.

## Struggles and rejected approaches

Repeating all detailed test-plan conditions in the sequence was rejected,
because it would create two competing sources of truth. The sequence instead
states its stop/go decisions and links to the formal test-plan criteria.

## Risks and follow-up

The rules do not supply missing measurements. Begin with unpowered T-01A and
keep all powered preload work gated until its documented prerequisites pass.

## Files

- `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`: added explicit stop/go rules.
- `docs/project/ENGINEERING_LOG.md`: recorded the documentation clarification.
