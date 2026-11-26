# Lab Note: 2026-11-26 - Direct Ethernet host-address recovery

## Objective

Restore the ioSender connection to the RP23CNC after a zero-byte
`App.config`, then determine why the restored sender configuration still failed
at the network transport.

## Configuration

- ioSender: `2.0.47`, installation at `C:\Users\jacks\Desktop\ioSender 2.0.47`
- Restored sender config: `ioSender-App.config.20261126-135637902`
- Restored config SHA-256:
  `D854D58D682E61DDBA996FBD335590D2CB176D5A4C2AFC9B9A72CC005587AAE1`
- Controller target: RP23CNC W5500 at `10.10.10.2:23`
- Host adapter: ASIX AX88178 USB2.0 adapter, Windows name `Ethernet 3`
- Adapter speed setting: `10BaseT Full_Duplex`
- Final host address: `10.10.10.100/24`, manually configured
- Operating system: Windows 11

## Code, commands, and configuration used

The validated ioSender configuration was restored with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\restore_iosender_config.ps1 -Launch
```

The first documented host-address restoration was attempted in an elevated
PowerShell:

```powershell
Set-NetIPInterface -InterfaceAlias 'Ethernet 3' -AddressFamily IPv4 -Dhcp Disabled
Remove-NetIPAddress -InterfaceAlias 'Ethernet 3' -AddressFamily IPv4 -Confirm:$false
New-NetIPAddress -InterfaceAlias 'Ethernet 3' -AddressFamily IPv4 -IPAddress 10.10.10.1 -PrefixLength 24
Test-NetConnection 10.10.10.2 -Port 23
```

The working host-address recovery used:

```powershell
netsh interface ipv4 set address name="Ethernet 3" static 10.10.10.100 255.255.255.0
Start-Sleep -Seconds 5
Get-NetIPAddress -InterfaceAlias 'Ethernet 3' -AddressFamily IPv4
ping.exe -n 2 -w 1000 10.10.10.2
ping.exe -n 2 -w 1000 10.10.10.1
Test-NetConnection 10.10.10.2 -Port 23
```

## Procedure

1. Close ioSender and verify that the install `App.config` is non-empty XML.
2. Restore the newest validated ioSender backup.
3. Report the transport exception separately from the sender-config recovery.
4. Inspect the `Ethernet 3` link state, IPv4 addresses, routes, and neighbors.
5. Attempt the previously documented host address, `10.10.10.1/24`.
6. When that address does not remain usable, assign `10.10.10.100/24` on the
   same direct link.
7. Ping the controller and test TCP port 23 before reopening ioSender.
8. Reopen ioSender and confirm its connection state and custom toolbar macros.

## Results

The restored `App.config` was 5,001 bytes and its SHA-256 matched the validated
backup. It contained:

- target `10.10.10.2:23`;
- `HOME + REGISTER` -> `G65 P113`;
- `PEN UP + PARK` -> `G65 P116`.

The host adapter reported `Status: Up`, `LinkSpeed: 10 Mbps`,
`MediaConnectionState: Connected`, and `FullDuplex: True` throughout the
network diagnosis.

The attempted `10.10.10.1/24` address was initially returned with
`AddressState: Invalid`. A later inspection found only the APIPA address
`169.254.21.161/16`; the manual address and the `10.10.10.0/24` route were
gone. Ping and TCP tests to `10.10.10.2` failed in that state.

After assigning `10.10.10.100/24`:

- `Get-NetIPAddress` reported `10.10.10.100`, prefix `24`,
  `PrefixOrigin: Manual`, `AddressState: Preferred`;
- `ping 10.10.10.2` returned 2/2 replies at 1 ms, TTL 255;
- a TCP connection to `10.10.10.2:23` succeeded;
- ioSender reopened with the restored macros and connected in `IDLE`;
- `10.10.10.1` did not answer ping and had an incomplete neighbor entry.

## Difficulties and corrective actions

- The zero-byte sender configuration was a separate ioSender fault. The
  validated backup restored it byte-for-byte.
- The later `CurrentDomainException` was a transport failure, not another
  corrupt configuration. The adapter had no usable `10.10.10.0/24` address.
- The documented `.1` host address did not remain usable on this Windows
  session. The host was moved to `.100` in the same subnet and the controller
  responded immediately. The exact cause of the `.1` rejection was not
  established.
- The direct link is physically healthy, so neither a cable replacement nor a
  controller settings restore was justified.

## Interpretation

The W5500 and controller network endpoint were already operational at
`10.10.10.2`. The failure was isolated to the Windows host's IPv4 assignment.
Any usable host address in `10.10.10.0/24` reaches the controller over this
direct link; the controller's gateway value does not need to equal the current
host address for same-subnet traffic.

## Decisions and next action

Keep `10.10.10.100/24` as the current host address. The controller remains at
`10.10.10.2`; no controller setting was changed.

After the next reboot, confirm that the host assignment remains `Preferred`
and that ioSender reconnects. Do not retest `.1` while the machine is in active
use; if that clean-up is desired, schedule it as a separate controlled network
test.

## Related records

- Change note:
  [`RPSW-20261126-001`](../../changes/rp23cnc-software/2026/2026-11-26-direct-ethernet-host-address-recovery.md)
- Wiring record: COM-002 in
  [`WIRING_TABLE.md`](../../hardware/WIRING_TABLE.md)
- Engineering log:
  [`elog-20261126-direct-ethernet-host-address-recovery`](../../project/ENGINEERING_LOG.md#elog-20261126-direct-ethernet-host-address-recovery)
