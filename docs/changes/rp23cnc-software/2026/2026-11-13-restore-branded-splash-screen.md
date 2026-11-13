---
id: RPSW-20261113-004
date: 2026-11-13
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: verified
components:
  - hmi/index.html
  - hmi/styles.css
  - hmi/app.js
  - hmi/assets/cmy-ring-v12.png
  - hmi/tests/smoke.cjs
tags:
  - touchscreen
  - hmi
  - splash-screen
  - inactivity-timeout
  - branding
  - cmy
  - accessibility
related:
  - RPSW-20261113-003
---

# Restore the branded startup and inactivity splash

## Summary

The browser HMI now uses the preserved cyan-magenta-yellow ring artwork for a
full-screen startup splash and for the configured inactivity timeout. The
splash retains the `XYθ`, `CONTROL`, precision-motion, touch-to-continue, and
explicit simulation/offline context from the prior operator console.

## Reason

The initial browser replacement had no startup splash. The brightness/timeout
follow-up added a functional but plain dark overlay, which lost the visual
identity and timeout presentation the owner valued in the earlier QML UI.

## Implementation

- Copied the existing 620×620 `cmy-ring-v12.png` asset into the web HMI rather
  than recreating it in CSS.
- Added a six-second CSS rotation around a stationary `XYθ` core, with the
  central disc masking the artwork center.
- Added matching `CONTROL`, `PRECISION MOTION / OPERATOR CONSOLE`, status, mode,
  and `TOUCH ANYWHERE TO CONTINUE` typography.
- The startup splash clears on touch/keyboard input or automatically after four
  seconds.
- The inactivity splash uses the same visual with
  `DISPLAY INACTIVITY TIMEOUT`, lock-state messaging, and amber emphasis.
- Any pointer/keyboard input dismisses the timeout and restarts the idle timer.
- Rotation is disabled under `prefers-reduced-motion`.

## Verification

- The copied asset matches the source on RPI4-HMI:
  SHA-256 `119d7d359a7bbe081db629e9c1e81281a45ced906592b30ca3e9bcbafb9ee818`.
- Native 720×1280 startup and timeout screenshots were inspected. The startup
  screen shows the rotating CMY ring and initialization text; the timeout
  screen shows the amber timeout state over the same identity.
- A one-minute timeout was exercised with Chromium virtual time and then
  restored to the stored five-minute setting.
- `node hmi/tests/smoke.cjs` verifies startup auto-dismissal, timeout display,
  and touch dismissal alongside the existing 17-view navigation suite.

## Struggles and rejected approaches

- Recreating the glow in CSS was rejected because the existing asset already
  captures the approved appearance and is only 78 KiB.
- Keeping the plain text-only timeout overlay was rejected because it discarded
  the operator-console identity.
- Requiring touch with no fallback was rejected for startup; the four-second
  automatic transition prevents an unattended boot from remaining blocked.

## Risks and follow-up

- Physical touch dismissal and multi-hour animation stability remain open.
- The timeout cover visually dims the screen but does not reduce the panel
  backlight. That distinction is intentional so returning to the HMI does not
  overwrite the operator-selected brightness.

## Files

- `hmi/index.html`: splash structure and text.
- `hmi/styles.css`: CMY-ring layout, rotation, timeout styling, and reduced-motion
  behavior.
- `hmi/app.js`: startup/touch dismissal and timeout state.
- `hmi/assets/cmy-ring-v12.png`: preserved approved artwork.
- `hmi/tests/smoke.cjs`: startup and timeout regression coverage.
- `hmi/README.md` and `camera-inspection/touchscreen.md`: current behavior.
