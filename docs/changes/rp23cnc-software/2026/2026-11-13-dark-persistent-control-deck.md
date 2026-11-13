---
id: RPSW-20261113-008
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
  - feed-override
  - dark-theme
  - user-experience
related:
  - RPSW-20261113-006
  - RPSW-20261113-007
---

# Use a dark background for the persistent control deck

## Summary

The entire fixed feed/transport deck now uses a black operator-console
background. Feed labels are light, feed controls are dark buttons, and
Start/Pause/Stop retain their green/amber/red identity colors.

## Reason

The previous QML operator console visually separated persistent machine controls
with a dark deck. The browser version used a white deck that blended into page
content and weakened the distinction between navigation surfaces and machine
commands.

## Implementation

- Changed the complete transport row background to black `#000`.
- Added a dark top border and stronger upward shadow.
- Changed feed labels, percentage, step controls, and reset styling for contrast.
- Kept Start/Pause/Stop color semantics and muted disabled colors unchanged.
- Left page content, app bar, DRO, and footer in the existing light theme.

## Verification

- A native 720×1280 screenshot confirms the black deck separates cleanly from
  the light page and footer, with readable feed controls.
- `node hmi/tests/smoke.cjs` passes all 16 views and prior feed, transport,
  settings, and splash behavior.
- The deployed kiosk remains active and returns HTTP 200.

## Struggles and rejected approaches

- Making only the Start/Pause/Stop button row dark was rejected because the feed
  controls are part of the same persistent machine-control area.
- Making the whole HMI dark was rejected; the owner requested the persistent
  control area specifically.

## Risks and follow-up

- Physical contrast in the final enclosure and room lighting remains an
  on-device acceptance check.

## Files

- `hmi/styles.css`: dark persistent deck and feed-control contrast.
- `hmi/README.md`: current operator-console visual state.
