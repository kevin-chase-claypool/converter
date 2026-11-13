---
id: RPSW-20261113-005
date: 2026-11-13
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: verified
components:
  - hmi/app.js
  - hmi/styles.css
  - hmi/tests/smoke.cjs
tags:
  - touchscreen
  - hmi
  - navigation
  - machine-tools
  - user-experience
  - information-architecture
related:
  - RPSW-20261113-001
---

# Group Machine tools by operator intent

## Summary

The flat Machine tools page is now divided into three visible subsections:
**Inspection & alignment**, **Machine setup**, and **Host & diagnostics**. All
seven destinations, Back behavior, and dedicated detail pages are unchanged.

## Reason

Owner review found the single uninterrupted tool list difficult to scan on the
portrait touchscreen. Group headings make related tasks easier to locate while
preserving the hierarchical interface and avoiding another level of taps.

## Implementation

- **Inspection & alignment:** optical registration, fiducial diagnostics, and
  camera.
- **Machine setup:** pen/homing/macros and coordinate references.
- **Host & diagnostics:** Pi settings/power and system diagnostics.
- Each group has a concise operator-intent heading and secondary description.
- Added a `3 groups` summary badge and consistent vertical grouping styles.
- No route, page title, command availability, or safety behavior changed.

## Verification

- `node hmi/tests/smoke.cjs` verifies exactly three tool groups, each group
  heading, and the existing 17-view navigation.
- A native 720×1280 screenshot confirms all seven large touch targets fit with
  the fixed DRO, transport strip, and footer, without horizontal overflow.
- The active Pi kiosk returned HTTP 200 after deployment.

## Struggles and rejected approaches

- Adding a second hierarchical Tools landing page was rejected because it would
  add another tap for every tool without reducing the number of choices.
- Persistent tabs or a drawer were rejected because they conflict with the
  established hierarchical navigation.
- Renaming or moving destinations was deferred; this change only improves
  information architecture and preserves learned paths.

## Risks and follow-up

- Future tool additions should be assigned to one of these three groups rather
  than recreating a flat list.
- Physical finger testing remains open, although all group rows retain the
  existing large navigation targets.

## Files

- `hmi/app.js`: grouped Machine tools markup and headings.
- `hmi/styles.css`: subsection heading and spacing styles.
- `hmi/tests/smoke.cjs`: three-group regression coverage.
- `hmi/README.md` and `camera-inspection/touchscreen.md`: current navigation
  tree.
