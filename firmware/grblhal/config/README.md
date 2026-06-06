# grblHAL Machine Configuration

Store controller-specific, reproducible configuration here.

Planned files:

- `build-record.md` - grblHAL and driver commits, board target, plugins, build date, UF2 checksum.
- `machine-settings.md` - annotated `$` settings and full settings dump.
- `pin-map.md` - RP23CNC revision, connector pins, signal polarity, and destination.
- `ethernet.md` - network settings and host connection procedure.

Do not commit credentials or private network secrets.

Initial axis convention:

| grblHAL axis | Machine axis | Unit |
|---|---|---|
| X | Gantry X | mm |
| Y | Gantry Y | mm |
| A | Bed motor shaft | degrees |
