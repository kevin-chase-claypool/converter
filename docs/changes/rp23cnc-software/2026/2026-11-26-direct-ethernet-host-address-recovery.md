---
id: RPSW-20261126-001
date: 2026-11-26
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
  - hardware
status: verified
components:
  - docs/hardware/WIRING_TABLE.md
  - firmware/grblhal/config/ethernet.md
  - firmware/grblhal/config/machine-settings.md
  - firmware/README.md
  - docs/report/lab-notes/2026-11-26-direct-ethernet-host-address-recovery.md
tags:
  - grblhal
  - ethernet
  - w5500
  - iosender
  - network
  - static-ip
  - recovery
  - app-config
related:
  - RPSW-20260928-001
  - WSW-20261025-001
---

# Restore direct Ethernet access after host-address loss

## Summary

ioSender is connected to RP23CNC at `10.10.10.2:23` in `IDLE`. The validated
sender configuration was restored, and the Windows host address was changed
from the documented `.1` to `10.10.10.100/24` within the same direct-link
subnet.

## Reason

A zero-byte ioSender `App.config` caused the known startup warning. Restoring
the validated backup recovered the target address and both toolbar macros, but
ioSender then reported `CurrentDomainException` because the controller was
unreachable.

The physical link remained connected at 10 Mbps full duplex, but the Windows
`Ethernet 3` adapter had no usable `10.10.10.0/24` address. The documented
`.1` assignment was returned as `Invalid`, then disappeared and left the
adapter on APIPA.

## Implementation

- Restored the validated 2026-11-26 ioSender backup and confirmed the active
  file matched its SHA-256.
- Set the host adapter to `10.10.10.100/24` with DHCP disabled.
- Kept the controller endpoint and controller-persistent settings unchanged.
- Added `firmware/grblhal/config/ethernet.md` as the current host-link record
  and recovery procedure.
- Corrected the wiring and firmware current-state documents to distinguish the
  controller address from the host source address.

## Verification

- `Ethernet 3`: `Up`, 10 Mbps, full duplex, media connected.
- Host IPv4: `10.10.10.100/24`, `Manual`, `Preferred`.
- `ping 10.10.10.2`: 2/2 replies, 1 ms, TTL 255.
- TCP `10.10.10.2:23`: connected successfully.
- ioSender 2.0.47: state `IDLE`; **HOME + REGISTER** and
  **PEN UP + PARK** visible.
- `10.10.10.1`: ping timed out and its IPv4 neighbor entry was incomplete.

See the
[2026-11-26 host-address recovery lab note](../../../report/lab-notes/2026-11-26-direct-ethernet-host-address-recovery.md).

## Struggles and rejected approaches

- The first ioSender exception was initially interpreted as a transport
  problem; the host adapter state confirmed it.
- Reapplying the documented `10.10.10.1/24` address did not result in a
  persistent usable address on this Windows session. `.100` in the same subnet
  was stable and reached the controller immediately.
- Restoring controller settings or changing the W5500 was rejected because the
  controller answered normally at `10.10.10.2` once the host had a route.

## Risks and follow-up

- Confirm after reboot that `.100/24` remains `Preferred`.
- The controller keeps gateway `$303=10.10.10.1`; this does not affect
  same-subnet host traffic, but the `.1` assignment failure remains unresolved.
- Restoring ioSender `App.config` does not deploy the updated P100 macro.
  Controller macro upload and the repeat `G65 P113` check remain pending.
- ioSender can still produce its zero-byte configuration fault; retain the
  startup backup and restore procedure.

## Files

- `firmware/grblhal/config/ethernet.md`: current host-link addressing and
  recovery procedure.
- `firmware/grblhal/config/machine-settings.md`: separates controller network
  settings from the current host source address.
- `docs/hardware/WIRING_TABLE.md`: updates the authoritative communication row
  and revision log.
- `firmware/README.md` and
  `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: record that
  connectivity is restored while P100 deployment remains pending.
- `firmware/grblhal/macros/README.md`: updates the current macro-deployment
  status.
- `docs/report/lab-notes/2026-11-26-direct-ethernet-host-address-recovery.md`:
  commands, observations, and corrective actions.
