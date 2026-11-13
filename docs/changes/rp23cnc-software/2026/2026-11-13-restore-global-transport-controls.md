---
id: RPSW-20261113-002
date: 2026-11-13
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: verified
components:
  - hmi/index.html
  - hmi/styles.css
  - hmi/app.js
  - hmi/tests/smoke.cjs
tags:
  - touchscreen
  - hmi
  - user-experience
  - transport-controls
  - start
  - pause
  - stop
  - accessibility
related:
  - RPSW-20261113-001
---

# Restore persistent transport controls on every HMI screen

## Summary

The hierarchical HMI now keeps a fixed **Start/Resume · Pause · Stop** transport
strip visible beneath the scrolling screen body. The operator no longer needs
to navigate back to Run to pause or stop an active job.

## Reason

The first browser HMI preserved hierarchical navigation but moved transport
actions into Run and showed only Hold/Stop in the header during an active
simulation. The project owner identified this as an operator-experience
regression compared with the previous native QML console, where the transport
deck remained visible.

## Implementation

- Added a dedicated transport row to the application shell. It participates in
  the layout grid, so it cannot cover scrolling content.
- The first action is Start while idle and Resume while held. The middle action
  is Pause while running. Stop is enabled while running or held.
- Pause retains the existing feed-hold behavior; it is only the operator-facing
  label. It does not imply cancellation.
- Removed the duplicate Hold/Stop controls from the app bar and the duplicate
  Start/Hold/Stop row from Run content.
- Transport actions remain disabled outside demo mode until a verified
  sender/supervisor state is connected. Stop retains its confirmation dialog.
- Improved the disabled transport colors so inactive Pause and Stop actions
  remain readable against the light theme.

## Verification

- `node hmi/tests/smoke.cjs` passes. The expanded smoke coverage checks that
  Start, Pause, and Stop are present on all 16 views, Start works from System,
  Pause transitions to Resume, and Stop can be opened from Tools and cancelled.
- `node --check hmi/app.js` and the scoped `git diff --check` pass.
- Native 720×1280 screenshots were inspected for the fixed control strip and
  scrolling content.
- The updated files were installed on RPI4-HMI with HTTP `200 OK` and one
  active Chromium kiosk. A live 720×1280 Chromium check verified the global
  transport strip, coordinate-level touch on Start, Pause-to-Resume, navigation
  to Tools with the transport still present, and Stop-dialog cancellation.

## Struggles and rejected approaches

- Restoring the old four persistent tabs was rejected because it would undo the
  requested Android-style hierarchy.
- Keeping both the app-bar quick actions and a transport strip would duplicate
  machine controls and split state-dependent labels.
- A floating transport overlay was rejected because it could cover functional
  controls near the bottom of long screens.

## Risks and follow-up

- Pause must map to an acknowledged feed hold rather than abort when the real
  sender adapter is implemented.
- Physical finger testing and cold-boot persistence remain open.
- The fixed strip reduces the scrolling viewport by 68 CSS pixels; all screens
  retain vertical scrolling, but future dense screens must avoid assuming the
  previous content height.

## Files

- `hmi/index.html`: adds the dedicated transport row.
- `hmi/styles.css`: reserves a fixed grid row and improves disabled contrast.
- `hmi/app.js`: renders state-aware transport controls globally and removes
  duplicate controls from the app bar and Run card.
- `hmi/tests/smoke.cjs`: covers all-view presence and state transitions.
- `hmi/README.md` and `camera-inspection/touchscreen.md`: record the operator
  control contract and navigation exception.
