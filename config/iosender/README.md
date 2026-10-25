# ioSender configuration backup

`ioSender-App.config` is a committed, validated snapshot of ioSender 2.0.47's
operator settings. It preserves the direct Ethernet address
`10.10.10.2:23`, the `HOME + REGISTER` and `PEN UP + PARK` macros, and the
remaining ioSender preferences.

This file is an ioSender-side backup only. The grblHAL `$` settings, G54
offsets, controller macros, and toolhead configuration remain in the
controller and are not replaced by an ioSender config restore.

The matching controller recovery snapshot from 2026-10-25 is stored in
`firmware/grblhal/config/settings-2026-10-25.txt` and
`firmware/grblhal/config/offsets-2026-10-25.nc`. The offsets file is a guarded
program containing an `M0` warning and G28/G30 checks; read it before running
it and confirm the machine is homed and clear.

## Backup

Double-click `backup-iosender-config.bat` in the repository root, or run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\backup_iosender_config.ps1
```

After deliberately changing grblHAL settings, first press **Settings: Grbl >
Backup** in ioSender so `settings.txt` and `offsets.nc` are refreshed, then run
the backup command. Changing ioSender macros only requires the backup command.

The script validates that the source is non-empty XML with a `<Config>` root
and writes timestamped copies plus `ioSender-App.config.latest` to:

- `%OneDrive%\ioSender Backups`
- `%LOCALAPPDATA%\Theta\ioSender-Backups`

It never replaces an existing backup when the source config is empty or
invalid. If the ioSender install folder contains the sender-generated
`settings.txt` or `offsets.nc`, their timestamped and `.latest` copies are
included in the same backup run.

## Automatic backup

Run once:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\install_iosender_config_backup_startup.ps1
```

This installs **ioSender Config Backup.cmd** in the current user's Startup
folder. It validates and snapshots the config at every Windows sign-in. If the
current config is already empty or invalid, the script refuses to overwrite the
last good backup. Remove it later with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\install_iosender_config_backup_startup.ps1 -Remove
```

## Restore

Close ioSender, then double-click `restore-iosender-config.bat` in the
repository root. The script:

1. Chooses the newest validated backup.
2. Preserves the existing `App.config` with a `.before-restore-*` suffix.
3. Restores the backup and verifies its SHA-256 hash.
4. Starts ioSender.

The committed snapshot is a final fallback that can be selected explicitly:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\restore_iosender_config.ps1 `
  -Backup config\iosender\ioSender-App.config -Launch
```
