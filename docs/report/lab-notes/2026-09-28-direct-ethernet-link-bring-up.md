# Lab Note: 2026-09-28 - Direct host-to-controller Ethernet link

## Objective

Establish an Ethernet link between the host PC and the RP23CNC with no router in
the path, so the host can reach the controller's Telnet service and a second
client can read the controller while ioSender owns the USB port.

## Configuration

- Controller: RP23CNC / `RP23U5XBB` V1.01, grblHAL 1.1f build `20260908`,
  Wiz850io (W5500) module.
- Host adapter: Plugable `USB2-E1000` (ASIX AX88178), driver `1.14.3.8`,
  Windows interface `Ethernet 3`.
- Cable: crossover, module RJ45 to adapter RJ45. No switch, no router.
- Host address: `10.10.10.1/24`, DHCP disabled.
- Controller address: `$301=0`, `$302=10.10.10.2`, `$303=10.10.10.1`,
  `$304=255.255.255.0`.

## Code, commands, and configuration used

```powershell
# Host side (Administrator)
Set-NetAdapterAdvancedProperty -Name 'Ethernet 3' -RegistryKeyword '*SpeedDuplex' -RegistryValue 2
Set-NetIPInterface -InterfaceAlias 'Ethernet 3' -Dhcp Disabled
Remove-NetIPAddress -InterfaceAlias 'Ethernet 3' -AddressFamily IPv4 -Confirm:$false
New-NetIPAddress -InterfaceAlias 'Ethernet 3' -IPAddress 10.10.10.1 -PrefixLength 24
```

```text
# Controller side, ioSender console over USB
$301=0
$302=10.10.10.2
$303=10.10.10.1
$304=255.255.255.0
then power-cycle the controller
```

## Observations

**Speed dependence.** The link only comes up with the adapter forced to
`10BaseT Full_Duplex` (`*SpeedDuplex` = 2). Every other combination failed with
the adapter reporting `Disconnected`, `0 bps`, zero bytes received, and the
module's LEDs showing green for roughly one second followed by a brief orange
flash:

| adapter setting | cable | result |
|---|---|---|
| AutoSense | straight | no link |
| 100BaseTx Full_Duplex | straight | no link |
| 100BaseTx Full_Duplex | crossover | no link |
| AutoSense | crossover | no link |
| **10BaseT Full_Duplex** | **crossover** | **link, green solid, orange blinking** |

Both devices link normally to a router or switch port on their own: the adapter
negotiated 1 Gbps to the router, and the module links to the router with a solid
green LED. The AX88178 and the W5500 therefore refuse each other at 100 Mbps and
at auto-negotiation, and agree only at 10 Mbps.

**Containment.** Because the module's W5500 does not implement auto-MDIX, a
direct connection needs a crossover cable; a switch port crosses internally and
does not.

**Reachability.** With the addresses above, `ping 10.10.10.2` returned 2/2
replies at 1-3 ms, TTL 255. Telnet (23), HTTP (80), and FTP (21) all accepted
connections, and a Telnet session returned the grblHAL banner
`GrblHAL 1.1f ['$' or '$HELP' for help]` plus `?` status reports.

**Concurrent access.** A Telnet connection succeeded while ioSender held the USB
port exclusively - `COM9` was denied to a second serial client at the same time.
The host therefore has two independent paths to the controller: USB for ioSender
and Ethernet for another client.

## Result

The direct host-to-controller Ethernet link is operational at 10 Mbps full
duplex with a crossover cable, at `10.10.10.2`, with no router in the path.

## Notes and next steps

- The controller's network settings are persistent. Returning it to the house
  network requires `$301=1` (DHCP) and a power cycle.
- 10 Mbps is roughly three orders of magnitude more bandwidth than G-code
  streaming requires, so the link speed is not a limitation.
- Whether the controller accepts a second Telnet client while ioSender is itself
  connected over Ethernet is untested; the verified configuration keeps ioSender
  on USB.
- The `10BaseT Full_Duplex` requirement is a property of this adapter, not the
  machine. A modern adapter with working auto-negotiation should link at
  100 Mbps with the same cable.
