---
id: HW-20260810-004
date: 2026-08-10
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - docs/testing/RECOMMENDED_TEST_SEQUENCE.md
  - docs/testing/TEST_PLAN.md
tags:
  - test-plan
  - safety
  - sequencing
related:
  - docs/testing/TEST_PLAN.md
  - E-05
  - E-17
  - E-18
---

# Record Recommended System Test Sequence

## Summary

Added a separate recommended order of operations for the project's bench,
controller, toolhead, motion, and integration tests.

## Reason

The formal test plan contains pass conditions but does not impose a single
dependency order. A recorded sequence reduces the chance of powering or
mechanically loading unverified hardware.

## Implementation

`docs/testing/RECOMMENDED_TEST_SEQUENCE.md` orders existing test IDs without
changing their scope or completion state. `TEST_PLAN.md` links to it and
remains the source of truth for pass conditions and results.

## Verification

- Reviewed every referenced ID against `docs/testing/TEST_PLAN.md`.
- Documentation index validation is recorded with this session.

## Struggles and rejected approaches

- Did not reorder or mark formal tests complete: test execution must remain
  evidence-based and is recorded in the worksheet/lab notes.

## Risks and follow-up

- Exact controller terminal behavior remains unverified until F-05 and the
  installed portion of E-18.
- Update the sequence if hardware architecture or test dependencies change.

## Files

- `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`: new recommended test order.
- `docs/testing/TEST_PLAN.md`: link to the sequence.
