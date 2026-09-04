# ADR-005: Treat Pulse Response as Per-Tool During Preflight

- Status: accepted for implementation; commissioning gated
- Date: 2026-09-04

## Context

The N20, lead screw, spring, rail, and carriage establish actuator motion, but
the force produced by a given motor pulse also depends on the installed pen or
pencil. Tip compliance, mass, clamp height, friction, and contact geometry can
change the force response. A single pulse-to-force table would therefore be
wrong for interchangeable tools.

## Decision

- T-01E establishes global actuator limits: minimum repeatable pulse, maximum
  safe pulse, direction/backlash behavior, response delay, and settle time.
- T-01J performs a short bounded response check for each installed tool and
  records its selected force target, contact/release thresholds, and any
  necessary pulse override.
- The load-cell reading remains the authority for contact and force hold. The
  pulse-response map is a tuning and safety bound, not an open-loop force
  command.
- A full T-01E pulse map is not repeated for every tool unless a tool falls
  outside the established actuator range or fails its preflight.

## Consequences

- Adding a new pen or pencil requires the normal P100/tool preflight, not a
  shared pen-tip-height datum or a complete actuator re-characterization.
- Global firmware limits can remain conservative while per-tool targets and
  bounded overrides account for tool-to-tool differences.
- A tool that cannot contact, release, or hold within the global limits remains
  disabled until its mount or profile is corrected.
- T-01F must distinguish global actuator values from per-tool settings before
  T-03 force-loop tuning is accepted.
