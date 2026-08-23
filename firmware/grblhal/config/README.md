# grblHAL Machine Configuration

Store controller-specific, reproducible configuration here.

Planned files:

- `build-record.md` - grblHAL and driver commits, board target, plugins, build date, UF2 checksum.
- `machine-settings.md` - annotated `$` settings and full settings dump.
- `pin-map.md` - firmware-facing mirror of the verified RP23CNC assignments in
  `docs/hardware/WIRING_TABLE.md`.
- `ethernet.md` - network settings and host connection procedure.

Do not commit credentials or private network secrets.

The verified baseline remains in [`build-record.md`](build-record.md). The
unflashed probe/expression configuration for staged magnetic-homing tests is in
[`homing-candidate.md`](homing-candidate.md); it must not replace the baseline
artifact until its motorless gates pass.

The master physical wiring record is
[`../../../docs/hardware/WIRING_TABLE.md`](../../../docs/hardware/WIRING_TABLE.md).
Update it first; this folder should contain only the controller-specific subset
needed to reproduce the firmware configuration.

Upstream board reference:
[`phil-barrett/RP23CNC`](https://github.com/phil-barrett/RP23CNC).

Initial axis convention:

| grblHAL axis | Machine axis | Unit |
|---|---|---|
| X | Gantry X | mm |
| Y | Gantry Y | mm |
| A | Bed motor shaft | degrees |
