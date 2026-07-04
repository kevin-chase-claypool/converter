---
id: WSW-20260607-002
date: 2026-06-07
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: verified
components:
  - AGENTS.md
  - docs/START_HERE.md
tags:
  - maintainability
  - technical-debt
  - documentation
  - project-policy
related:
  - WSW-20260607-001
---

# Continuous Maintainability Policy

## Summary

Long-term maintainability and evidence-based optimization are now mandatory
parts of every future project task.

## Reason

The project will accumulate software, firmware, hardware, and documentation
complexity over time. Depending on conversational memory would make cleanup
inconsistent across new threads and contributors.

## Implementation

The root working agreement now requires focused cleanup when touched code has
become difficult to modify, explicit tracking of larger technical debt,
proportional verification, removal of confirmed obsolete material, and
periodic review of duplication, module size, stale documentation, generated
artifacts, and unresolved TODOs.

It also prohibits broad speculative rewrites. Optimization must improve the
project's understandability, verifiability, operation, or extensibility.

## Verification

- Confirmed the policy exists in root `AGENTS.md`, which applies to future
  threads opened in this repository.
- Confirmed onboarding links contributors to that working agreement.
- Validated local Markdown links and `git diff --check`.

## Struggles and rejected approaches

The requirement was initially stated only in conversation. That was rejected
as insufficient because conversational context is not reliably available in a
new thread.

## Risks and follow-up

The policy guides future work but does not justify unrelated refactoring during
every task. Larger cleanup must remain scoped, documented, and independently
verifiable.

## Files

- `AGENTS.md`: permanent maintainability requirements.
- `docs/START_HERE.md`: onboarding summary.
- `docs/project/ENGINEERING_LOG.md`: chronological audit record.
