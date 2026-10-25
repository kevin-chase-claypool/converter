---
id: WSW-20261025-001
date: 2026-10-25
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
components:
  - config/iosender/ioSender-App.config
  - tools/backup_iosender_config.ps1
  - tools/restore_iosender_config.ps1
  - tools/install_iosender_config_backup_startup.ps1
  - backup-iosender-config.bat
  - restore-iosender-config.bat
  - firmware/grblhal/config/settings-2026-10-25.txt
  - firmware/grblhal/config/offsets-2026-10-25.nc
tags:
  - iosender
  - configuration
  - backup
  - restore
  - macros
  - grblhal
  - offsets
status: implemented
related:
  - 2026-09-28-direct-ethernet-link-bring-up
---

# Add ioSender configuration recovery

## Summary

Added a validated, cloud-backed ioSender `App.config` snapshot plus manual and
automatic backup/restore utilities. The same recovery set includes a complete
live grblHAL `$$` settings dump and controller offsets.

The committed ioSender snapshot preserves these toolbar commands:

- **HOME + REGISTER (F1)** -> `G65 P113`
- **PEN UP + PARK (F2)** -> `G65 P116`
- Direct Ethernet connection `10.10.10.2:23`

## Reason

ioSender 2.0.47 found a zero-byte `App.config` and could not save a replacement
because its failed XML load left the same file open. The sender eventually
started with a new configuration, but its custom macro buttons were gone.
There was no independent backup, and the incident could have cost the
operator's sender settings during a long machine session.

ioSender's `App.config` is independent of grblHAL's `$` settings and offsets,
so a sender recovery file alone would not protect the complete controller
configuration.

## Implementation

- `backup_iosender_config.ps1` auto-discovers the running ioSender install,
  requires non-empty `<Config>` XML, verifies the copied SHA-256, and writes
  timestamped and latest snapshots to OneDrive and local application data.
- `restore_iosender_config.ps1` refuses to restore into a running ioSender
  installation, preserves the current target before replacement, and verifies
  the restored hash.
- `install_iosender_config_backup_startup.ps1` installs a current-user Startup
  entry that backs up the config at each Windows sign-in. This was selected
  after Windows denied scheduled-task registration in the active session.
- Root-level batch files provide one-click backup and restore.
- `config/iosender/ioSender-App.config` is the committed recovery snapshot.
- ioSender's **Settings: Grbl > Backup** action produced the complete
  `settings.txt` and `offsets.nc`; validated copies are committed under
  `firmware/grblhal/config/`.
- The `offsets.nc` restore program is retained verbatim, including its `M0`
  warning and G28/G30 position checks. It must not be streamed blindly.

## Verification

- Four Python regression tests cover valid backup, invalid-source refusal,
  restore-with-preservation, and startup-entry installation/removal.
- Full converter discovery passes `523` tests with one expected
  OpenGL-context skip.
- The live backup run reports two macros and writes matching copies to:
  - `C:\Users\jacks\OneDrive\ioSender Backups`
  - `C:\Users\jacks\AppData\Local\Theta\ioSender-Backups`
- The committed ioSender snapshot matches the active config:
  `970CA403A17B071039AF921DB3F7F50EA5018C5B8BD75E71219C2DB63CCADAFF`.
- Full controller settings snapshot:
  `E7596CC158F75FE1B149BB77600D428356EE496BC2091151DD19C08249ADCC10`.
- Controller offsets snapshot:
  `AB1F05D6EA42EB376B571B383FC67A0F10430C92C0001ED1E558D8A89AE4F8B9`.
- ioSender was reopened on the restored config and connected to
  `10.10.10.2:23` in `IDLE`; both macros are visible in the toolbar.

## Struggles and rejected approaches

- The initial installer used Windows Task Scheduler, but current-user task
  registration was denied in this environment. The installer was replaced
  with the no-admin Startup-folder approach.
- A second Ethernet Telnet connection cannot capture `$$` while ioSender owns
  the connection. The existing ioSender **Settings: Grbl > Backup** action was
  used instead.

## Risks and follow-up

- Startup backup runs only at sign-in. Run the one-click backup after changing
  ioSender macros or controller settings.
- The committed settings and offsets are a dated snapshot, not live sync. A
  later deliberate calibration change requires a new snapshot and commit.
- Restoring `App.config` does not restore controller `$` settings, and restoring
  controller settings does not restore the sender configuration. Use the
  correct recovery file for each layer.
- Verify a future `$$` backup after the next deliberate settings change; F-06
  power-cycle persistence still requires its own reboot test.

## Files

- `config/iosender/`: committed sender recovery snapshot and procedure.
- `tools/*iosender*`: backup, restore, and startup-install utilities.
- `software/tests/test_iosender_config_backup.py`: recovery regression tests.
- `firmware/grblhal/config/settings-2026-10-25.txt`: complete live settings.
- `firmware/grblhal/config/offsets-2026-10-25.nc`: controller work offsets and
  guarded restore program.
