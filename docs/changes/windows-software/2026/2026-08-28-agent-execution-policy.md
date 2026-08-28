---
id: WSW-20260828-001
date: 2026-08-28
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - AGENTS.md
  - docs/START_HERE.md
tags:
  - agent-workflow
  - token-efficiency
  - quality
  - project-policy
related:
  - WSW-20260607-002
---

# Establish sequential agent execution policy

## Summary

Established a cost-conscious agent workflow: Luna performs bounded routine
work, while Sol handles judgment-heavy decisions and reviews. Work is
sequential, and the flagship model is not used for unattended or overnight
runs.

## Reason

The project needs to reduce model-token use without weakening technical
quality, safety, or decision-making.

## Implementation

The root working agreement now defines the Luna/Sol responsibilities, the
evidence-based escalation boundary, one-job-at-a-time execution, and the ban
on overnight, unattended, recurring, or long-running Sol work. The onboarding
document summarizes the policy for new sessions.

## Verification

- Confirmed the policy and onboarding summary are present in `AGENTS.md` and
  `docs/START_HERE.md`.
- Ran `python tools\docs_index.py --write` and
  `python tools\docs_index.py --check`.

## Struggles and rejected approaches

None. The policy is deliberately specific enough to prevent routine tasks from
using the flagship model while preserving escalation for material judgment.

## Risks and follow-up

Agent availability may vary by environment. Preserve the role boundaries even
if an equivalent available model must be substituted.

## Files

- `AGENTS.md`: canonical agent execution policy.
- `docs/START_HERE.md`: onboarding summary.
- `docs/project/ENGINEERING_LOG.md`: chronological policy record.
