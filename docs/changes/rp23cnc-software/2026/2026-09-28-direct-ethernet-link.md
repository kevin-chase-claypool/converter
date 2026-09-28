---
id: RPSW-20260928-001
date: 2026-09-28
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - firmware/grblhal/config/machine-settings.md
  - docs/hardware/WIRING_TABLE.md
tags:
  - grblhal
  - ethernet
  - w5500
  - network
  - telnet
  - static-ip
related:
  - E-16
  - F-01
---

# Direct host-to-controller Ethernet link at 10 Mbps

## Summary

The RP23CNC is reachable over Ethernet from the host with no router in the path,
at `10.10.10.2`. A second client can read the controller over Telnet while
ioSender keeps the USB port.

## Reason

The host needed two independent paths to the controller. ioSender owns the USB
port exclusively, so anything else - the live progress tracker in particular -
needs a network path. A router in the path was undesirable, and the earlier
attempt to use a straight cable failed at the physical layer.

The W5500 in the installed Wiz850io module does not implement auto-MDIX, so a
direct connection needs a crossover cable: the module links normally to a switch
or router port, which crosses internally, but not to another device port over a
straight cable.

## Implementation

Host side, adapter `Ethernet 3` (ASIX AX88178):

- `*SpeedDuplex` = `2` (`10BaseT Full_Duplex`).
- Static `10.10.10.1/24`, DHCP disabled.

Controller side, `grblHAL` network settings:

| Setting | Value |
|---|---|
| `$301` | `0` - static rather than DHCP |
| `$302` | `10.10.10.2` |
| `$303` | `10.10.10.1` |
| `$304` | `255.255.255.0` |

`10.10.10.0/24` was chosen because the house network occupies
`192.168.4.0/22`, which already covers `192.168.4.0` through `192.168.7.255`;
the controller's own static default of `192.168.5.1` sits inside that range and
would have put the adapter and Wi-Fi in overlapping address space.

## Verification

See
[`2026-09-28-direct-ethernet-link-bring-up.md`](../../../report/lab-notes/2026-09-28-direct-ethernet-link-bring-up.md).

- Link: `Ethernet 3` `Up` at **10 Mbps**, `MediaConnectionState: Connected`.
- `ping 10.10.10.2`: 2/2 replies, 1-3 ms, TTL 255.
- Telnet 23, HTTP 80, and FTP 21 all accept connections.
- A Telnet session returned the grblHAL banner and answered `?` with status
  reports, while a second serial client was denied `COM9` because ioSender held
  it.

## Struggles and rejected approaches

Four combinations were tried before one worked; the table is in the lab note.
AutoSense and 100 Mbps both fail against the module, and both cable types fail
at 100 Mbps, so neither the cable nor the speed alone explains it - the two PHYs
only agree at 10 Mbps.

Two theories that did not survive contact with the hardware: that the adapter's
2010 driver was at fault (it links to the router at 1 Gbps), and that the module
was defective (it links to the router with a solid green LED).

## Risks and follow-up

- The controller's network settings are persistent. It will not appear on the
  house network again until `$301=1` (DHCP) plus a power cycle.
- The 10 Mbps requirement is a property of this specific adapter. A modern
  adapter with working auto-negotiation should link at 100 Mbps over the same
  cable; the link speed is not otherwise a limitation, since G-code streaming
  uses a tiny fraction of 10 Mbps.
- Whether grblHAL accepts a second Telnet client while ioSender is connected
  over Ethernet rather than USB is untested. The verified arrangement keeps
  ioSender on USB.
- The 4,875-subpath and 5,243-subpath artwork cases that motivated the network
  path are unaffected by this change; the tracker work remains open.

## Files

- `firmware/grblhal/config/machine-settings.md`: records the network settings.
- `docs/hardware/WIRING_TABLE.md`: records the crossover host link.
- `docs/report/lab-notes/2026-09-28-direct-ethernet-link-bring-up.md`: evidence.
