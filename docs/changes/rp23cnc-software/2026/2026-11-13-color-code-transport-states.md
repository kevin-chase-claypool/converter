---
id: RPSW-20261113-007
date: 2026-11-13
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: verified
components:
  - hmi/styles.css
tags:
  - touchscreen
  - hmi
  - transport-controls
  - color
  - disabled-state
  - user-experience
related:
  - RPSW-20261113-002
  - RPSW-20261113-006
---

# Retain transport action colors while disabled

## Summary

Start/Resume remains green, Pause remains amber, and Stop remains red in both
enabled and disabled states. Disabled actions use slightly muted versions of
their identity colors rather than the shared grey disabled style.

## Reason

The previous QML console used distinct green, yellow, and red transport
backgrounds. The browser HMI preserved those colors only while actions were
enabled; idle Pause and Stop collapsed into the same grey, weakening immediate
recognition and visual continuity.

## Implementation

- Added transport-specific disabled backgrounds for green, amber, and red
  actions.
- Disabled labels remain readable while the buttons keep their safety/action
  identity.
- Feed controls retain their neutral styling; only machine transport actions are
  color-coded.
- No enabled-state action, confirmation, or availability rule changed.

## Verification

- A native 720×1280 idle-state screenshot confirms green Start, amber Pause, and
  red Stop remain visually distinct while Pause and Stop are disabled.
- `node hmi/tests/smoke.cjs` continues to pass all 16 views and prior transport,
  feed, settings, and splash behavior.
- The deployed Pi kiosk remains active and returns HTTP 200.

## Struggles and rejected approaches

- Keeping the shared grey disabled background was rejected because it erased
  the operator's learned action-color mapping.
- Reducing opacity on fully saturated active colors was rejected because it
  made disabled labels difficult to read.

## Risks and follow-up

- Physical color perception and sunlight contrast remain on-device checks.
- Future transport actions should use these semantic colors only for their
  established meanings: green start/resume, amber pause/hold, red stop.

## Files

- `hmi/styles.css`: transport-specific disabled color rules.
- `hmi/README.md`: current transport visual-state contract.
