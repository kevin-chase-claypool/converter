---
id: RPSW-20261025-001
date: 2026-10-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P116.macro
  - firmware/grblhal/macros/controller-manifest-2026-10-25.txt
  - config/iosender/ioSender-App.config
tags:
  - iosender
  - p116
  - macro
  - ftp
  - deployment
  - error-84
related:
  - WSW-20261025-001
  - RPSW-20260930-004
---

# Deploy the P116 pen-up and park macro

## Summary

Uploaded the repository's guarded `P116.macro` to the installed RP23CNC
controller. The ioSender **PEN UP + PARK** toolbar button now points to a
command that exists on the controller filesystem.

## Reason

The restarted ioSender configuration correctly contained
`PEN UP + PARK -> G65 P116`, but the controller console returned
`error:84 - Could not open file`. A binary FTP listing showed P100-P115 present
and P116 absent. The repository had developed P116 but the controller had not
been given the file.

## Implementation

- Validated all 17 repository macros with `tools\check_macros.py`; all passed.
- Uploaded the 2,543-byte `P116.macro` over binary FTP to `10.10.10.2`.
- The controller returned FTP status 226, and its post-upload directory listing
  reports the same 2,543-byte length as the repository source.
- Reproduced ioSender startup with the saved configuration connected at
  `10.10.10.2:23`; both toolbar macros remain visible and state is `IDLE`.

## Verification

- Local P116 SHA-256:
  `E08313848941C752D1733153C2C1B5A1382C732FF8C71965B52696A7F742338`.
- Controller listing retains P100-P116, recorded in
  `controller-manifest-2026-10-25.txt`.
- The first full P116 motion path still requires a supervised clean run:
  P115 clear proof, GP2 full retract, P111 home, and final G53 park.
- Five focused recovery tests and all `524` discovered converter tests pass,
  with one expected OpenGL-context skip.

## Struggles and rejected approaches

- The ioSender macro was initially suspected because it had just been restored,
  but the XML command and live console both prove it sent `G65 P116`.
- FTP retrieval timed out while the controller was connected, so remote content
  could not be independently hash-compared. Upload success and equal byte count
  are the deployment evidence.

## Risks and follow-up

- P116 previously caused a -Y overtravel before it was revised to home first.
  Do not execute the macro until the gantry and bed are clear and the operator
  is ready to stop power.
- A firmware update or controller filesystem replacement can remove the macro
  again. Keep `P116.macro` in the repository and verify the controller listing
  after any storage change.

## Files

- `firmware/grblhal/macros/P116.macro`: deployed source.
- `firmware/grblhal/macros/controller-manifest-2026-10-25.txt`: post-upload
  filesystem evidence.
- `docs/report/lab-notes/2026-10-25-p116-macro-deployment.md`: procedure and
  result.
