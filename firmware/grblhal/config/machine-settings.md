# RP23CNC grblHAL settings

Verified, evidence-backed settings for the installed RP23U5XBB controller.
This is not a complete `$$` dump: capturing that in full is still F-06. Only
record a value here once a dated lab note or the wiring table supports it.

Board: `RP23U5XBB` V1.01. See [`build-record.md`](build-record.md) for the
firmware artifact, checksum, and boot report.

## Spindle / tool output

| Setting | Value | Meaning | Evidence |
|---|---|---|---|
| `$16` | `1` | Invert spindle signals, bit 0 = **spindle enable** | F-05, 2026-09-23: the RP23CNC spindle `ENA` output is active-high by default, which drove the toolhead's active-low optocoupler input on at idle and made the pen dive at power-up. `$16=1` inverts the enable so `M3` pulls it low and `M5` leaves it high. Reboot-required. |

The optocoupler input is active-low by design: `ENA` low lights U1, whose
collector pulls `GP29` low, which the toolhead reads as `M3`. With `$16=1`, the
fail-safe direction is preserved — any loss of controller power or optocoupler
current leaves `GP29` high (pen up).

## Control inputs

| Setting | Value | Meaning | Evidence |
|---|---|---|---|
| `$14` | `6` | Invert control inputs: Feed hold + Cycle start (E-stop clear) | E-19, 2026-09-08: matches the NC SW1 E-stop wiring. Live E-19 press/release verification remains open. |

## Probe

| Setting | Value | Meaning | Evidence |
|---|---|---|---|
| `$6` | `1` | Invert probe signal | F-08 / E-18, 2026-09-10: installed normally-open PRB sink. Restored to `$20=1` and `G90` at completion. |

## Network

| Setting | Value | Meaning | Evidence |
|---|---|---|---|
| `$300` | `grblHAL` | Hostname | 2026-09-28 direct-link bring-up; build default |
| `$301` | `0` | IP mode: static, using `$302` (`1` is DHCP) | 2026-09-28: set together with `$302`-`$304` for the router-free host link |
| `$302` | `10.10.10.2` | Static IP address | 2026-09-28: `10.10.10.1/24` host, crossover cable, no router |
| `$303` | `10.10.10.1` | Gateway (the host; unused on a direct link) | 2026-09-28 |
| `$304` | `255.255.255.0` | Netmask | 2026-09-28 |
| `$305` | `23` | Telnet port | 2026-09-28: answered with the grblHAL banner and status reports |
| `$307` | `80` | HTTP port | 2026-09-28: accepted a connection |
| `$308` | `21` | FTP port | 2026-09-28: accepted a connection |

These values are **persistent**. The controller is on a fixed `10.10.10.x`
address and will not appear on the house network until `$301` is returned to `1`
(DHCP) and the board is power-cycled.

## Limits and homing (from the unloaded commission snapshot)

| Setting | Value | Meaning |
|---|---|---|
| `$20` / `$21` | `1` / `0` | Soft limits enabled (X/Y); hard-limit alarms disabled |
| `$40` | `1` | Soft limits apply to jogging |
| `$22` / `$23` | `3` / `2` | X/Y homing enabled with single-axis diagnostics; Y homes negative |
| `$24` / `$25` / `$27` | `50` / `500` / `10.000` | Locate rate, seek rate, pull-off (mm/min, mm) |
| `$43` / `$44` / `$45`-`$47` | `1` / `XY` / `none` | One XY-only homing phase; Z and A excluded |
| `$100` | `80.00000` | X steps/mm |
| `$101` | `80.000000` | Y steps/mm |
| `$110` / `$111` | `1500` | Preliminary unloaded X/Y max rate (mm/min) |
| `$120` / `$121` | `500` | Preliminary unloaded X/Y acceleration (mm/sec^2) |
| `$130` / `$131` | `455.000` / `446.000` | Conservative X/Y software envelope (mm) |
| `$133` | `0.000` | Continuous A bed: no finite maximum travel |

These motion values are the unloaded commissioning snapshot in
[`build-record.md`](build-record.md); they are not a pen-loaded plotting limit.
