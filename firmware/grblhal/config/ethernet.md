# RP23CNC Ethernet Configuration

This is the current-state record for the direct host-to-controller Ethernet
link. The controller remains at its documented address; only the Windows host
address changed after its previous static assignment was rejected.

## Current addressing

| Side | Address | Evidence |
|---|---|---|
| Host PC, `Ethernet 3` | `10.10.10.100/24`, manual | Preferred on 2026-11-26; controller ping and Telnet verified |
| Controller W5500 | `10.10.10.2/24`, static (`$301=0`) | Ping returned 2/2 replies at 1 ms; ioSender reached `IDLE` |
| Controller gateway setting | `10.10.10.1` (`$303`) | Retained from the 2026-09-28 direct-link setup; not currently assigned to the host |

The host adapter is the Plugable USB2-E1000 AX88178 interface named
`Ethernet 3`. It remains forced to `10BaseT Full_Duplex` and links at
10 Mbps through the crossover cable.

## Why the host uses `.100`

The 2026-09-28 link used host address `10.10.10.1/24`. On 2026-11-26, an
elevated Windows attempt to restore that address reported
`AddressState Invalid`; the address then disappeared and Windows returned to
APIPA `169.254.21.161`. There was no route to `10.10.10.2`, and ioSender
reported a transport exception while trying to connect.

Using `10.10.10.100/24` on the same adapter produced a stable `Preferred`
address immediately. The controller still responds at `10.10.10.2`. The exact
reason Windows rejected `.1` is unresolved, so do not replace the working
address merely to restore the older documentation text.

## Host recovery

Run in an elevated PowerShell while ioSender is closed:

```powershell
netsh interface ipv4 set address name="Ethernet 3" static 10.10.10.100 255.255.255.0
Start-Sleep -Seconds 5
Get-NetIPAddress -InterfaceAlias 'Ethernet 3' -AddressFamily IPv4
ping.exe -n 2 -w 1000 10.10.10.2
Test-NetConnection 10.10.10.2 -Port 23
```

Accept the link only when:

- the host address is `Preferred`;
- `10.10.10.2` returns ping replies;
- Telnet port `23` reports `TcpTestSucceeded : True`.

Then open ioSender. Its restored `App.config` targets `10.10.10.2:23`.

## Controller configuration

The persistent controller network settings and their evidence are maintained
in [`machine-settings.md`](machine-settings.md). Do not restore controller
`$` settings or G54 offsets to repair a host adapter problem.

The W5500 does not implement auto-MDIX; use a crossover cable or a switch port.
The 10 Mbps requirement belongs to this specific AX88178 adapter, not the
controller.

## Evidence

- 2026-09-28 initial direct-link bring-up:
  [`2026-09-28-direct-ethernet-link-bring-up.md`](../../../docs/report/lab-notes/2026-09-28-direct-ethernet-link-bring-up.md)
- 2026-11-26 host-address recovery:
  [`2026-11-26-direct-ethernet-host-address-recovery.md`](../../../docs/report/lab-notes/2026-11-26-direct-ethernet-host-address-recovery.md)
