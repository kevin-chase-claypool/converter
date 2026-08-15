# Pro Micro JST Harness

This is the current toolhead signal-harness plan. It minimizes detachable
connectors while requiring each board's connector pins to be physically
consecutive on the SparkFun Pro Micro RP2350 header.

## J-DRV: DRV8833 logic, 1×4

| Pin | Pro Micro pin | DRV8833 connection |
|---:|---|---|
| 1 | `GP4` | `IN1` |
| 2 | `GP5` | `IN2` |
| 3 | `GP6` | `EEP` / protection-fault output |
| 4 | `GP7` | `ULT` / low-true sleep input |

The DRV8833's separate 6 V power connector must include `GND`; that ground is
also the required reference for the four logic signals. Do not put motor power
or motor leads in J-DRV.

> **Exact installed module:** the ACEIRMC `B08RMWTDLM` module labels `ULT` as
> its sleep input (low = sleep) and `EEP` as its protection/fault output. The
> installed, continuity-checked harness already matches those functions:
> `GP7` drives `ULT` and `GP6` reads `EEP`. The firmware uses this same mapping;
> no driver-end rewiring is required. Inspect the board's `J2` solder bridge
> before relying on direct `ULT` sleep control; the seller notes that the bridge
> may need to be opened for that feature.

## J-PC817: PC817 tool-side interface, 1×6

Use the consecutive right-side Pro Micro holes, descending from `GND`:

| Pin | Pro Micro pin | Function | PC817 terminal |
|---:|---|---|---|
| 1 | `GND` | `TOOL_GND` | J2.4 |
| 2 | `RST` | **NC; no wire at either end** | — |
| 3 | `3V3` | `TOOL_3V3` | J2.2 |
| 4 | `GP29` / `A3` | U1 M3/M5 / ENA input | J2.1 |
| 5 | `GP28` / `A2` | U2 `HOME_ARM` / AUX0 input | J2.3 |
| 6 | `GP27` / `A1` | U3 `A_HOME` output | J2.6 |

`RST` is present only because it lies between `GND` and `3V3`; it is not a
spare signal and must remain unconnected. `GP27`–`GP29` are ADC-capable but are
valid 3.3 V digital GPIOs in this design.

## Connector pitch and isolation

The Pro Micro through holes are 2.54 mm pitch. A genuine JST-XH header is
2.50 mm pitch and must not be forced into those holes. Use a 2.54 mm
JST-compatible connector system or a small adapter/pigtail for genuine JST-XH.

`TOOL_GND` belongs only to the toolhead side. Never add `CTRL_GND` to J-PC817;
the PC817 board's galvanic isolation depends on the two grounds remaining
separate.

## Required verification after repinning

The earlier E-18 bench results were collected on GP8/GP9/GPIO20. Repeat the
U1, U2, U3, and `CTRL_GND`/`TOOL_GND` isolation checks using GP29/GP28/GP27
after the harness and firmware are changed.
